import logging
import threading
from string import punctuation
from collections import Counter
import random

import requests
from bs4 import BeautifulSoup
import feedparser
from newspaper import Article
from newspaper.article import ArticleException

from interfaces import IIntent_slot
from environment import Environment


def pick_random_sentence(options):
    """Randomly picks and returns a sentence among the options list. Enables to
    randomize a bit what the AI says"""
    return random.choice(options)


class News(IIntent_slot):

    def __init__(self):

        self._env = Environment.get_instance()

        self.intent_id = "news"
        logging.debug("Creating intent slot '" + self.intent_id + "'")
        self.lang = self._env.language
        self.__nlp = self._env.language_model
        self.__news_are_ready = False
        self.__stop_running = False

        if self.lang == "en": self.__sources = self._env.config["NEWS"]["sources_en"].split(",")
        elif self.lang == "fr": self.__sources = self._env.config["NEWS"]["sources_fr"].split(",")
        else: raise ValueError("Wrong language code")

        for i in range(len(self.__sources)):
            self.__sources[i] = self.__sources[i].strip()
            logging.info(f"RSS feed registered: {self.__sources[i]}")

        self.__summaries_count = int(self._env.config["NEWS"]["summaries_count"])
        self.__desired_duration = int(self._env.config["NEWS"]["desired_duration"])

        self.__news_bulletin = []
        self.__news_bulletin_as_string = ""

        # The news bulletin is prepared in a separate thread so that the program
        # does not hang for severla minutes
        th = threading.Thread(target=self.__prepare_news_bulletin)
        th.start()

    def run(self, input):

        logging.debug("Running intent slot '" + self.intent_id + "' with input '" + input + "'")

        if self.__news_are_ready:
            if not self.__news_bulletin_as_string:
                for s in self.__news_bulletin:
                    self.__news_bulletin_as_string = self.__news_bulletin_as_string + s["title"]
                    self.__news_bulletin_as_string = self.__news_bulletin_as_string + "\n"
                    self.__news_bulletin_as_string = self.__news_bulletin_as_string + s["summary"]
                    self.__news_bulletin_as_string = self.__news_bulletin_as_string + "\n\n"
            return (self.__news_bulletin_as_string, True)


        else:
            if self.lang == "en":
                potential_lines = ["Sorry, I am still going through today's news",
                                "The news are not ready yet",
                                "Please wait a bit, I haven't finished preparing the news bulletin"]
            elif self.lang == "fr":
                potential_lines = ["Désolé, je suis encore en train de chercher les information du jour",
                                "Les informations ne sont pas encore prêtes",
                                "Attendez un peu, je n'ai pas fini de préparer le bulletin d'informations"]
            else: raise ValueError("Wrong language code")
            msg = pick_random_sentence(potential_lines)
            return (msg, True)

    def exit(self):
        """Sets stop_running at True so that any running thread can get the
        information and stop"""
        logging.debug("Exiting " + self.intent_id + ". Any remaining thread will be closed")
        self.__stop_running = True

    def __prepare_news_bulletin(self):

        raw_news = self.__collect_news(self.__sources)
        if self.__stop_running: return
        articles = self.__delete_duplicates(raw_news)
        if self.__stop_running: return
        articles = self.__sort_news(articles)
        if self.__stop_running: return
        self.__generate_summaries(articles)

        logging.info("News bulletin is ready")
        self.__news_are_ready = True

    def __collect_news(self, urls):

        """Here each piece of news is a dictionary. 'news' is the list containing all
        these dictionaries.
        Keys contained in each entry:
        "title": the article's title
        "content": the article itself
        "date": the article's publication date (optional)
        "source": the url of the feed where the article was listed"""

        logging.info("Downloading articles from the provided RSS feeds")
        news = []

        assert (isinstance(urls, list)), f"""News.__collect_news takes a
        list as parameter, not {type(urls)}"""

        for url in urls:

            news_feed = feedparser.parse(url) # Parsing the RSS feed

            for item in news_feed.entries:

                if self.__stop_running: return news

                if "title" not in item or "link" not in item:
                    logging.warning(f"RSS feed at URL {url} does not follow proper formatting and some of its items cannot be processed")
                    continue

                info = {}

                info["title"] = item.title
                content = self.__retrieve_news_content(item.link)
                if not content:
                    continue
                    # We just skip to the next article if we can't
                    # retrieve this one, for whatever reason

                info["content"] = content

                try:
                    info["date"] = item.published
                except AttributeError:
                    info["date"] = False

                info["source"] = url

                news.append(info)

            # Here we do some cleaning by removing from the article's some
            # text that might be displayed right before of after it, such as
            # popups, ads, prompts to get the user to subscribe...

            if len(news) not in (0,1):

                prefix = ""
                end_of_prefix = False
                for i in range(len(news[0]["content"])):
                    for j in news:
                        if j["content"][i] != news[0]["content"][i]:
                            end_of_prefix = True
                            break
                    if end_of_prefix: break
                    prefix += news[0]["content"][i]


                if len(prefix) >= 100:
                    for n in news:
                        n["content"] = n["content"].removeprefix(prefix)

                suffix = ""
                end_of_suffix = False
                for i in range(1, len(news[0]["content"])):
                    for j in news:
                        if j["content"][-i] != news[0]["content"][-i]:
                            end_of_suffix = True
                            break
                    if end_of_suffix: break
                    suffix = news[0]["content"][-i] + suffix

                if len(suffix) >= 100:
                    for n in news:
                        n["content"] = n["content"].removesuffix(suffix)

        return news

    def __filter_page_text(self, text_elements):

        """ !!! Should not be called from outside the class !!!
        This function sorts the page's p tags in order to get rid of the ones
        containing text not related to the article such as ads, pictures' captions...)
        This is not 100% accurate, and some unwanted text might still remain """

        filtered_text_elements = []

        for e in text_elements:
            ignore_this_element = False
            parent_tags = e.parents
            for p in parent_tags:
                if p.name in ("a", "header", "footer", "li", "ul", "ol") :
                    ignore_this_element = True
                    break

            if len(filtered_text_elements) != 0:
                if not (filtered_text_elements[-1].parent == e.parent or len(e.get_text()) >= 45):
                    continue
            else:
                if len(e.get_text()) < 100: continue

            if not ignore_this_element:
                filtered_text_elements.append(e)

        return filtered_text_elements


    def __retrieve_news_content(self, url):

        """!!! Should not be called from outside the class !!!
        This function retrieves the main content on the webpage whose url is passed
        as a parameter"""

        try:

            # We first try to extract the article using the newspaper module
            # (https://newspaper.readthedocs.io/en/latest/). Only if it fails
            # to retrieve properly the text do we do that with BeautifulSoup
            article = Article(url)
            article.download()
            article.parse()

            text = article.text
            if len(text) > 1200: return text

        except ArticleException: pass

        r = requests.get(url)

        if not r:
            logging.warning(f"Unable to retrieve content from URL {url}")
            return False

        soup = BeautifulSoup(r.text, 'html.parser')


        text_elements = soup.find_all("p")
        text_elements = self.__filter_page_text(text_elements)
        content = ""
        for t in text_elements:
            content += t.get_text()
            content += "\n"

        # A text too short indicates either that the article isn't very useful, or
        # that we failed to extract all of it. In any case, if that happens we
        # do not return it
        if len(content) > 1200: return content
        else: return False


    def __delete_duplicates(self, articles):

        """Some articles might talk about the same thing, especially if they come
        from different sources. This function tries to get rid of duplicates"""

        selected_articles = []
        rejected_articles = []

        # Similarity is calculated by spacy based on semantics
        # For more details, see spacy's doc
        similarity_threshold = 0.72

        for article_1 in articles:

            if (article_1 in rejected_articles): continue

            raw_title_1 = self.__nlp(article_1["title"])
            title_1 = self.__nlp(' '.join([str(t) for t in raw_title_1 if (not t.is_stop and t.pos_ in ['NOUN', 'PROPN', 'VERB'])]))

            for article_2 in articles:

                if self.__stop_running: return selected_articles
                if (article_2 in selected_articles
                    or article_2 in rejected_articles
                    or article_1 is article_2): continue

                raw_title_2 = self.__nlp(article_2["title"])
                title_2 = self.__nlp(' '.join([str(t) for t in raw_title_2 if (not t.is_stop and t.pos_ in ['NOUN', 'PROPN', 'VERB'])]))

                if title_1.similarity(title_2) >= similarity_threshold:
                    if len(article_1["content"]) >= len(article_2["content"]):
                        rejected_articles.append(article_2)
                    else:
                        rejected_articles.append(article_1)
                        break

            if article_1 not in rejected_articles: selected_articles.append(article_1)

        return selected_articles

    def __sort_news(self, articles):

        """Sort the news to get the most important ones first.
        This function is based on the assumption that the websites where the articles
        come from will tend to put the "most important" articles first in their RSS feeds,
        hence the fact that we take the first article of each source one by one,
        alternating between the sources."""

        articles_by_source = {}
        sorted_news = []

        total_articles_count = len(articles)

        for a in articles:

            if a["source"] not in articles_by_source: articles_by_source[a["source"]] = []
            articles_by_source[a["source"]].append(a)


        processed_articles = 0
        current_index = 0

        while processed_articles < total_articles_count:
            if self.__stop_running: return sorted_news
            for a in articles_by_source:
                try:
                    sorted_news.append(articles_by_source[a][current_index])
                    processed_articles += 1

                except IndexError: pass
            current_index += 1

        return sorted_news



    def __generate_summaries(self, articles):

        """summaries_count: number of summaries to generate, if enough news are available
        desired_duration: average duration of each summaries in seconds. It might be less if an
        article is too short
        Return value: a dictionary with the keys 'title', 'summary', 'date' and 'source'"""

        logging.info("Generating summaries from the downloaded news articles")

        summaries_count = self.__summaries_count
        desired_duration = self.__desired_duration

        assert (isinstance(desired_duration, int)), f"""News_preparator.generate_summaries:
        desired_duration parameter must be an int, not {type(desired_duration)}"""

        desired_words_count = desired_duration*3
        pos_tags = ['PROPN', 'ADJ', 'NOUN', 'VERB', 'NUM']

        summaries = []

        for i in range(summaries_count):
            if self.__stop_running: return
            keywords = []
            try:
                doc = self.__nlp(articles[i]["content"].lower())

            except IndexError:
                break

            for token in doc:
                if(token.text in self.__nlp.Defaults.stop_words or token.text in punctuation):
                    continue
                if(token.pos_ in pos_tags):
                    keywords.append(token.text)

            freq_words = Counter(keywords)
            max_freq = Counter(keywords).most_common(1)[0][1]
            for w in freq_words:
                freq_words[w] = (freq_words[w]/max_freq)

            sentences_importance = {}
            for sent in doc.sents:
                for word in sent:
                    if word.text in freq_words.keys():
                        if sent in sentences_importance.keys():
                            sentences_importance[sent] += freq_words[word.text]
                        else:
                            sentences_importance[sent] = freq_words[word.text]

            top_sentences = sorted(sentences_importance.items(), key=lambda kv: kv[1], reverse=True)

            summary = []
            words_counter = 0
            for j in range(len(top_sentences)):
                summary.append(str(top_sentences[j][0]).strip(' \n').capitalize())
                sentence_length = len(str(top_sentences[j][0]).split())
                words_counter += sentence_length

                if 0.95*desired_words_count <= words_counter: break

            self.__news_bulletin.append({'title': articles[i]['title'],
                            'summary': " ".join(summary),
                            'date': articles[i]['date'],
                            'source': articles[i]['source']})
