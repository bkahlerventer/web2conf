# coding: utf8

def index(): return plugin_flatpage()
def about(): return plugin_flatpage()
def venue(): return plugin_flatpage()
def maps(): return plugin_flatpage()
def schedule(): redirect(URL(c='schedule', f='index'))
def proposals(): return plugin_flatpage()
def lightning(): return plugin_flatpage()
def keynotes(): return plugin_flatpage()
def openspace(): return plugin_flatpage()
def tutorials(): return plugin_flatpage()
def staff(): return plugin_flatpage()
def talks(): redirect(URL(c='activity', f='accepted'))

def helpforspeakers(): return plugin_flatpage()
def ConferenceNights(): return plugin_flatpage()
