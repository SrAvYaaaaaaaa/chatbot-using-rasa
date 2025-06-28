# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []


from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import requests
from bs4 import BeautifulSoup as bs
from transformers import LEDTokenizer, LEDForConditionalGeneration, pipeline
import logging

def summarize_text(text):
  tokenizer = LEDTokenizer.from_pretrained("allenai/led-base-16384")
  model = LEDForConditionalGeneration.from_pretrained("allenai/led-base-16384")
  summarizer=pipeline('summarization', model=model,tokenizer=tokenizer)
  summary=summarizer(text,max_length=150, min_length=10,do_sample=False)
  summarized_text=summary[0]['summary_text']
  return summarized_text

def get_url(p):
  headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
  }
  url ="https://www.cgi.com/en/"
  html = requests.get(url,headers=headers)
  soup = bs(html.text, 'html.parser')
  content =soup.find_all(class_='keywords')
  for each in content:
    topics=each.find_all('a')
    for topic in topics:
      if p.lower() in topic.text.lower():
        url1='http://www.cgi.com'+topic.get('href')
        return url1
def get_page_content(url1):
  headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
  }
  html1=requests.get(url1, headers=headers)
  soup1 = bs(html1.text, 'html.parser')
  if soup1.header:
    soup1.header.decompose()
  if soup1.footer:
    soup1.footer.decompose()
  main_content = soup1.find('div', class_='page-standard')
  if main_content:
    text = main_content.get_text(separator=' ', strip=True)
    return text

class ActionSummarizeText(Action):
    def name(self) -> Text:
        return "action_summarize_text"
    def run(self,dispatcher: CollectingDispatcher,tracker:Tracker,domain:Dict[Text,Any]) -> List[Dict[Text, Any]]:
        addr=tracker.latest_message.get('text')
        if not addr:
            dispatcher.utter_message(text="No text found")
        else:
            url_addr=get_url(addr)
            summ=get_page_content(url_addr)
            summary=summarize_text(summ)
            dispatcher.utter_message(text=summary)
            dispatcher.utter_message(text=f"For further details visit {url_addr}")
        return [SlotSet("content",summ)]


class ActionHelloWorld(Action):
    def name(self) -> Text:
        return "action_say_answer"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        question= tracker.latest_message.get('text')
        context= tracker.get_slot('content')
        if not question or not context:
            dispatcher.utter_message(text="Sorry, The question you asked is out of scope of the website.")
        else:
            qa_pipeline=pipeline("question-answering")
            result=qa_pipeline(question=question,context=context)
            answer=result['answer']
            dispatcher.utter_message(text=f"The answer to your question is {answer}")

        return []