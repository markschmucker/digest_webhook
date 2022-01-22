# coding=utf-8

from datetime import datetime, timedelta
import dateutil.parser
from threading import Thread
from log import logger
import json
from sets import Set
from ses import send_digest_email, send_simple_email

transparent_image = '<img src="https://forum.506investorgroup.com/uploads/default/original/2X/7/75021bfe618e0d724ff14bd272528bf036a40633.png" alt="*" style="width:10px;height:10px;padding-top:0px;padding-bottom:0px;padding-left:0px;padding-right:0px;margin-top:0px;margin-bottom:0px;margin-left:0px;margin-right:0px;background-color:#%s">'

# Colored bullets
bullets = [
    'https://forum.506investorgroup.com/uploads/default/original/2X/3/30d42e29d80ee276d03dc30b3c7cbbbddf423d36.png',
    'https://forum.506investorgroup.com/uploads/default/original/2X/b/b81252ae174dfa6646fdfa70e6f465ebdddb51cc.png',
    'https://forum.506investorgroup.com/uploads/default/original/2X/e/e029f06cd0e6ff02714482cbe4502a50b77215e4.png',
    'https://forum.506investorgroup.com/uploads/default/original/2X/7/7763342ba2bc632367f2eb42c23cf135788a6667.png',
    'https://forum.506investorgroup.com/uploads/default/original/2X/8/8135366235230b1f8b683797b56c7691e6ece3b3.png',
    'https://forum.506investorgroup.com/uploads/default/original/2X/f/f7476b5173dd178a66f190156f4971b55c65eaf8.png',
    'https://forum.506investorgroup.com/uploads/default/original/2X/3/3546b2d4b26bd4279baaca08ecd779f2ad72770e.png',
    'https://forum.506investorgroup.com/uploads/default/original/2X/d/d92c2a79de373df890b4e8e86041c361e03272bd.png',
    'https://forum.506investorgroup.com/uploads/default/original/2X/6/62d54e2922409b7aa629814c547873055e9b1d66.png' # black
]


def get_bullet(cat):
    idx = 8
    if 'premium' in cat.lower():
        idx = 0
    elif 'equity' in cat.lower():
        idx = 1
    elif 'debt' in cat.lower():
        idx = 2
    elif 'alternative' in cat.lower():
        idx = 3
    elif 'sponsors' in cat.lower():
        idx = 4
    elif 'members' in cat.lower():
        idx = 5
    elif 'platforms' in cat.lower():
        idx = 6
    elif 'general' in cat.lower():
        idx = 7
    elif 'deals' in cat.lower():
        idx = 0
    print cat, idx
    return bullets[idx]



def cmp_topic_categories(x, y):
    return cmp(x['topic_categories'], y['topic_categories'])


def cmp_timestamp(x, y):
    return cmp(x['timestamp'], y['timestamp'])


class ProcessDigest(Thread):

    def __init__(self, data):
        """
        Period is a string starting with t or n and followed by a number. If t,
        the number is the number of minutes. If n, the number is the number of
        posts. This odd convention makes the web GUI easier.
        """

        Thread.__init__(self)
        self.data = data
        self.ordered_categories = []
        self.ordered_main_categories = []

    def shorten(self, text, chars=200):
        return text[:chars]

    def _spacify(self, txt):
        # replace long links with a placeholder, as they make various clients
        # do funny formatting
        start = txt.find('http')
        if start > -1:
            end = start
            while end < len(txt) and txt[end] not in [' ', ')']:
                end += 1
            txt = txt.replace(txt[start:end], "[long link, see forum]")

        start = txt.find('/upload')
        if start > -1:
            end = start
            while end < len(txt) and txt[end] not in [' ', ')']:
                end += 1
            txt = txt.replace(txt[start:end], "[long link, see forum]")

        return txt

    def spacify(self, txt):
        for attempt in range(5):
            txt = self._spacify(txt)
        return txt

    def post_to_html(self, post, topic, max_len=200):

        s = ''
        if post['raw']:
            created_at = dateutil.parser.parse(post['timestamp'])
            created_at -= timedelta(hours=5)
            date_str = created_at.strftime("%b %d %H:%M EST")

            s += '<b>'
            s += post['username']
            s += '</b>'
            s += ' '

            s += '<i>'
            s += 'in '
            s += '<b>'
            s += post['topic_title']
            s += '</b>'
            s += ','
            s += '</i>'
            s += ' '

            s += '<i>'
            s += date_str
            s += ': '
            s += '</i>'
            s += ' '

            s += self.shorten(self.spacify(post['raw']), max_len)
            s += ' '
            s += '<a href="%s">More...</a>' % post['url']

        s = '<p style="margin-top:5px;margin-bottom:5px">' + s + '</p>'
        return s

    def topic_to_linkname(self, topic):
        # links get truncated in some viewers if slug is too long
        return topic['slug'][:30]

    def make_topics_table(self, topics):

        html = ''

        # target for "back to top"
        html += '<a rel="nofollow" name="topic_table"></a>'

        for cat in self.ordered_categories:
            # Note topic_categories may be joined by now
            topics_in_cat = [t for t in topics if cat == t['topic_categories']]
            color = topics_in_cat[0]['topic_emblem_or_color']
            img = '<img src="%s" style="width:10px;height:10px;margin-right:6px;">' % get_bullet(cat)






            """
            html += '<span>'
            html += img
            html += ' '
            html += '<b>'
            html += cat
            html += '</b>'
            html += '</span>'
            """



            html += '<table>'
            html += '<tr>'
            html += '<td>'
            html += img
            html += '</td>'
            html += '<td>'
            html += '<b>'
            html += cat
            html += '</b>'
            html += '</td>'
            html += '</tr>'
            html += '</table>'






            html += '<ul style="margin-top:10px;margin-bottom:20px;">'
            for topic in topics_in_cat:
                html += '<li>'
                html += self.topic_to_link(topic)
                html += '</li>'
            html += '</ul>'

        return html


    def topic_to_html(self, topic):
        if topic['new_topic']:
            title = '[New Topic] ' + topic['topic_name']
        else:
            title = topic['topic_name']
        try:
            url = topic['posts'][0]['url']
        except Exception:
            url = topic['topic_url']
        cats = topic['topic_categories']
        tags = topic['topic_tags']
        color = topic['topic_emblem_or_color']
        # cats list has been joined to a string; join it with tags
        cats_and_tags = [cats] + tags
        img = '<img src="%s" style="width:10px;height:10px;margin-right:6px;">' % get_bullet(cats)

        # first a link so the top topics table can link to this topic
        html = '<a rel="nofollow" name="%s"></a>' % self.topic_to_linkname(topic)




        html += '<table>'

        # row for spacing
        html += '<tr height=20px;>'
        html += '<td>'
        html += ' '
        html += '</td>'
        html += '</tr>'

        # Topic title, with link to topic on forum
        html += '<tr>'

        html += '<td>'
        html += '<h3 style="margin-top:15px;margin-bottom:5px">'
        html += '<a style="text-decoration:none" href="%s">%s</a>' % (url, title)
        html += '</h3>'
        html += '</td>'
        html += '</tr>'

        html += '</table>'


        html += '<table>'

        # row for emblem, cats, and tags
        html += '<tr>'
        html += '<td>'

        html += img

        html += '</td>'

        html += '<td>'
        html += ' '
        html += ' | '.join(cats_and_tags)
        html += '</td>'

        html += '</tr>'
        html += '</table>'

        html += '<table>'

        topic['posts'].sort(cmp=cmp_timestamp)

        # Each post in the topic
        for post in topic['posts']:
            html += '<tr style = "padding-top:0px;padding-bottom:0px">'
            html += '<td style = "padding-top:0px;padding-bottom:0px">'
            html += self.post_to_html(post, topic)
            html += '</td>'
            html += '</tr>'

        # Back to top link
        html += '<tr>'
        html += '<td>'
        html += '<a rel="noreferrer" style="color:#1155cc; text-decoration:none;" href="#topic_table">Back to top</a>'
        html += '</td>'
        html += '</tr>'

        html += '</table>'
        return html

    def topic_to_link(self, topic):
        if topic['new_topic']:
            title = '[New Topic] ' + topic['topic_name']
        else:
            title = topic['topic_name']

        n = len(topic['posts'])
        if n < 2:
            pluralator = ''
        else:
            pluralator = 's'

        html = '<a rel="noreferrer" style="text-decoration:none" href="#%s">%s: %d update%s</a>' % (self.topic_to_linkname(topic), title, n, pluralator)
        return html

    def subject(self):
        freq_to_str = {
            30: '30 Minute ',
            60: '1 Hour ',
            180: '3 Hour ',
            1440: 'Daily ',
            4320: '3 Day ',
            10080: 'Weekly ',
        }
        s = freq_to_str.get(self.data.get('frequency'), '')
        return '[506] Investor Group %sSummary' % s

    def get_special_post(self):
        html = ''
        # Special post is optional in admin settings
        p = self.data.get('special_post')
        if p:
            if p['raw']:
                # Format with same method as other posts, but allow 500 chars
                h = self.post_to_html(p, 'Announcement', 500)
                caption = 'Featured Post'
                img = '<img src="%s" style="width:45px;height:45px;border-radius:50%%">' % p['avatar']

                # Add avatar and caption to the post
                html = '<table>'
                html += '<tr>'
                html += '<td>'
                html += img
                html += '</td>'
                html += '<td style="padding-left:20px">'
                html += '<div style="color:#%s">' % '888888'
                html += '<b>'
                html += caption
                html += '</b>'
                html += '</div>'
                html += h
                html += '</td>'
                html += '</tr>'
                html += '</table>'
        return html

    def get_favorite_post(self, p):
        html = ''
        if p['raw']:
            # Format with same method as other posts, but allow 500 chars
            h = self.post_to_html(p, 'Favorite', 500)
            img = '<img src="%s" style="width:45px;height:45px;border-radius:50%%">' % p['avatar']

            # Add avatar and caption to the post
            html = '<table>'
            html += '<tr>'
            html += '<td>'
            html += img
            html += '</td>'
            html += '<td style="padding-left:20px">'
            html += h
            html += '</td>'
            html += '</tr>'
            html += '</table>'
        return html

    def get_favorite_posts(self):
        html = ''
        posts = self.data.get('favorite_posts')
        if posts:
            caption = 'Today\'s Most-Liked Posts'
            html += '<div style="color:#%s">' % '888888'
            html += '<b>'
            html += caption
            html += '</b>'
            html += '</div>'
            for p in posts:
                html += self.get_favorite_post(p)
        return html

    def patch(self, topics):
        """ Pre-process the json for convenience """
        for topic in topics:
            # Add a flag indicating whether it's a new topic
            post_nums = [int(p['url'].split('/')[-1]) for p in topic['posts']]
            topic['new_topic'] = any([x==1 for x in post_nums])

            # I should not have modified topic_categories in place- I need the
            # original topic_categories, as a list. To ensure I don't break anything,
            # I'm saving it to a new key.
            topic['original_topic_categories'] = topic['topic_categories']

            topic['topic_categories'] = ' | '.join(topic['topic_categories'])

    def order_categories(self, topics):
        # Create a common ordering to be followed by the topics table and the posts.
        cats = [t['topic_categories'] for t in topics]
        # uniqify
        cats = list(Set(cats))
        cats.sort()
        self.ordered_categories = cats
        # This is along the right track, but also need first cat if pipe,
        # plus all if not pipe, then uniqify.
        a = [c for c in cats if '|' not in c]
        b = [c.split('|')[0].strip() for c in cats if '|' in c]
        self.ordered_main_categories = list(Set(a + b))
        self.ordered_main_categories.sort()
        # print self.ordered_main_categories

    def run(self):
        # Data is the json as dict
        data = self.data
        if data:
            
            # email before patching or otherwise messing with the data
            if data['email'] == 'markschmucker@yahoo.com':
                try:
                    send_simple_email('markschmucker@yahoo.com', 'json to debug', json.dumps(data))
                    logger.info(json.dumps(data))
                except Exception:
                    pass
            
            
            topics = data['activity']
            # print 'Digest.run got %s, %s, %d topics' % (data['username'], data['email'], len(topics))
            if topics:
                # Pre-processing for convenience
                self.patch(topics)
                self.order_categories(topics)

                num_visible_topics = len(topics)
                num_visible_posts = sum([len(t['posts']) for t in topics])

                post_contents = []
                for cat in self.ordered_main_categories:

                    # The duplicate topics are because of this line. When cat = Deals,
                    # and a topic's topic_categories is Premium Deals, then cat is in
                    # topic_categories. Need to check for equality, not containment.
                    # That's more complicated than it should be, because I've modified
                    # topic_categories in-place. I need to retain the original list,
                    # perhaps in a new key original_topic_categories, and change this
                    # line to test for equality of cat and original_topic_categories[0].
                    # Note cat is the *main* category.

                    # I can test using new json every day now, so no hurry.

                    # topics_in_cat = [t for t in topics if cat in t['topic_categories']]
                    # This fixes it in one case at least.
                    topics_in_cat = [t for t in topics if cat == t['original_topic_categories'][0]]


                    topics_in_cat.sort(cmp=cmp_topic_categories)
                    for topic in topics_in_cat:
                        post_content = self.topic_to_html(topic)
                        post_contents.append(post_content)

                username = data['username']
                summary = '<h3>%s, you have %d New Posts in %d Topics</h3>' % (username, num_visible_posts, num_visible_topics)
                subject = self.subject()
                posts_contents = ''.join(post_contents)
                topics_contents = self.make_topics_table(topics)

                special_contents = self.get_special_post()
                favorite_contents = self.get_favorite_posts()

                # dummy arg for now:
                manage_emails_url = ''

                email_address = data['email']


                recipients = ['markschmucker@yahoo.com',
                              'mhr.uncgolf@gmail.com',
                              'andrewgoldberg@gmail.com',
                              'dan.rudolph@live.com',
                              'robert.fakheri@gmail.com'
                              ]

                send_digest_email(email_address, topics_contents, posts_contents, summary, subject, manage_emails_url, special_contents, favorite_contents, username)

                logger.info('emailed %s %s' % (username, email_address))


if __name__ == '__main__':
    # f = file('t.json', 'rt')
    # s = f.read()
    # f.close()

    # from debug import s
    # d = json.loads(s, strict=False)

    with open('new.json', 'rt') as f:
        s = f.read()
        d = json.loads(s)

    d['username'] = 'admin'
    d['email'] = 'markschmucker@yahoo.com'

    t = ProcessDigest(d)
    t.start()

    # d = json.loads(s, strict=False)
    # d['username'] = 'JohnDoe'
    # d['email'] = 'markschmucker0@gmail.com'
    #
    # t = ProcessDigest(d)
    # t.start()
