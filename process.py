from datetime import datetime, timedelta
import dateutil.parser
from threading import Thread
from log import logger
import json
from sets import Set
from ses import send_digest_email

transparent_image = '<img src="https://forum.506investorgroup.com/uploads/default/original/2X/7/75021bfe618e0d724ff14bd272528bf036a40633.png" alt="*" style="width:10px;height:10px;padding-top:0px;padding-bottom:0px;padding-left:0px;padding-right:0px;margin-top:0px;margin-bottom:0px;margin-left:0px;margin-right:0px;background-color:#%s">'


class ProcessDigest(Thread):

    def __init__(self, data):
        """
        Period is a string starting with t or n and followed by a number. If t,
        the number is the number of minutes. If n, the number is the number of
        posts. This odd convention makes the web GUI easier.
        """

        Thread.__init__(self)
        self.data = data
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

            s += date_str
            s += ': '
            s += ' '

            s += self.shorten(self.spacify(post['raw']), max_len)
            s += ' '
            #s += post_url(post, topic) + '...'
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

        for cat in self.ordered_main_categories:
            # Note topic_categories may be joined by now
            topics_in_cat = [t for t in topics if cat == t['topic_categories']]
            color = topics_in_cat[0]['topic_emblem_or_color']

            html += '<table>'
            html += '<tr>'
            html += '<td>'

            # Paragraph makes it better in outlook
            html += '<p style="color:#%s;">' % '888888'

            # table, not span, works for color emblem in Outlook
            if 1:
                html += '<table style="width:10px;height:10px;padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px">'
                html += '<tr padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px>'
                html += '<td padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px>'
                html += transparent_image % color
                html += '</td>'
                html += '</tr>'
                html += '</table>'
            else:
                html += transparent_image % color

            html += '</p>'

            html += '</td>'

            html += '<td>'
            html += ' '
            html += '<b>'
            html += cat
            html += '</b>'

            html += '</td>'
            html += '</tr>'
            html += '</table>'

            html += '<ul>'
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
        url = topic['topic_url']
        cats = topic['topic_categories']
        tags = topic['topic_tags']
        color = topic['topic_emblem_or_color']
        # cats list has been joined to a string; join it with tags
        cats_and_tags = [cats] + tags

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


        # row for emblem, cats, and tags
        # This requires an inner table where column widths can be different from the outer table
        html += '<tr>'
        html += '<td>'
        html += '<table padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px>'
        html += '<tr>'
        html += '<td padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px;width=10px>'
        html += transparent_image % color
        html += '</td>'
        html += '<td padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px;text-align:left>'
        html += ' '
        html += ' | '.join(cats_and_tags)
        html += '</td>'
        html += '</tr>'
        html += '</table>'
        html += '</td>'
        html += '</tr>'

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
                caption = 'Important Announcement'
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
            caption = 'Today\'s Most-Liked Post'
            img = '<img src="%s" style="width:45px;height:45px;border-radius:50%%">' % p['avatar']

            # Add avatar and caption to the post
            html = '<table>'
            html += '<tr>'
            html += '<td>'
            html += img
            html += '</td>'
            html += '<td style="padding-left:20px">' # need to push this change, else most-liked will be grey
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

    def get_favorite_posts(self):
        html = ''
        posts = self.data.get('favorite_posts')
        if posts:
            for p in posts:
                html += self.get_favorite_post(p)
        return html

    def patch(self, topics):
        """ Pre-process the json for convenience """
        for topic in topics:
            # Add a flag indicating whether it's a new topic
            post_nums = [int(p['url'].split('/')[-1]) for p in topic['posts']]
            topic['new_topic'] = any([x==1 for x in post_nums])

            # Convert list of cats to single string so they break out by subcategory
            topic['topic_categories'] = ' | '.join(topic['topic_categories'])


    def order_categories(self, topics):
        # Create a common ordering to be followed by the topics table and the posts.
        cats = [t['topic_categories'] for t in topics]
        # uniqify
        cats = list(Set(cats))
        cats.sort()
        self.ordered_main_categories = cats

    def run(self):
        # Data is the json as dict
        data = self.data
        if data:
            topics = data['activity']
            print 'Digest.run got %s, %s, %d topics' % (data['username'], data['email'], len(topics))
            if topics:
                # Pre-processing for convenience
                self.patch(topics)
                self.order_categories(topics)

                num_visible_topics = len(topics)
                num_visible_posts = sum([len(t['posts']) for t in topics])

                post_contents = []
                for cat in self.ordered_main_categories:
                    topics_in_cat = [t for t in topics if cat in t['topic_categories']]
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

                if email_address not in recipients:
                    #print 'not emailing s', email_address
                    return

                send_digest_email(email_address, topics_contents, posts_contents, summary, subject, manage_emails_url, special_contents, favorite_contents, username)

                # also email to me, for now
                for email_address in ['markschmucker@yahoo.com', 'markschmucker0@gmail.com', 'admin506@protonmail.com']:
                   send_digest_email(email_address, topics_contents, posts_contents, summary, subject, manage_emails_url, special_contents, favorite_contents, username)

                logger.info('emailed %s %s' % (username, email_address))


if __name__ == '__main__':
    f = file('t.json', 'rt')
    s = f.read()
    f.close()

    d = json.loads(s)
    d['username'] = 'admin'
    d['email'] = 'markschmucker@yahoo.com'

    if 1:
        t = ProcessDigest(d)
        t.start()
    else:
        import requests
        resp = requests.post('http://digests.506investorgroup.com:8081', json=d)
        print resp
