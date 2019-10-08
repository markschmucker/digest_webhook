from datetime import datetime, timedelta
import dateutil.parser
from threading import Thread
from log import logger
import json
from sets import Set
from ses import send_digest_email

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
            html += '<table style="width:10px;height:10px;padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px;background-color:#%s">' % color
            html += '<tr padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px>'
            html += '<td padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px>'
            html += '</td>'
            html += '</tr>'
            html += '</table>'

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
        html += '<tr>'
        html += '<td>'

        # Color emblem is surprisingly hard to get square in Outlook. Recommended approach
        # is to use the background color of a table.
        html += '<table style="padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px">'
        html += '<tr>'
        html += '<td>'
        html += '<table style="width:10px;height:10px;padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px;background-color:#%s">' % color
        html += '<tr padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px>'
        html += '<td padding-top:0px;padding-bottom:0px;margin-top:0px;margin-bottom:0px>'
        html += '</td>'
        html += '</tr>'
        html += '</table>'

        html += '</td>'

        html += '<td>'
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

    def get_testimonial(self):
        html = ''
        # Special post is optional in admin settings
        p = self.data.get('special_post')
        if p:
            if p['raw']:
                # Format with same method as other posts, but allow 500 chars
                h = self.post_to_html(p, 'Featured', 500)
                caption = 'Featured Post'
                img = '<img src="%s" style="width:45px;height:45px;border-radius:50%%">' % p['avatar']

                # Add avatar and caption to the post
                html = '<table>'
                html += '<tr>'
                html += '<td>'
                html += img
                html += '</td>'
                html += '<td style="padding-left:20px">'
                html += caption
                html += h
                html += '</td>'
                html += '</tr>'
                html += '</table>'
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

                featured_contents = self.get_testimonial()

                # dummy arg for now:
                manage_emails_url = ''

                email_address = data['email']
                template = 'template.html'



                recipients = ['markschmucker@yahoo.com',
                              'mhr.uncgolf@gmail.com',
                              'andrewgoldberg@gmail.com',
                              'dan.rudolph@live.com',
                              'robert.fakheri@gmail.com'
                              ]

                if email_address not in recipients:
                    #print 'not emailing s', email_address
                    return

                send_digest_email(email_address, topics_contents, posts_contents, summary, subject, manage_emails_url, template, featured_contents, username)

                # also email to me, for now

                email_address = 'markschmucker@yahoo.com'
                send_digest_email(email_address, topics_contents, posts_contents, summary, subject, manage_emails_url, template, featured_contents, username)

                email_address = 'markschmucker0@gmail.com'
                send_digest_email(email_address, topics_contents, posts_contents, summary, subject, manage_emails_url, template, featured_contents, username)

                email_address = 'admin506@protonmail.com'
                send_digest_email(email_address, topics_contents, posts_contents, summary, subject, manage_emails_url, template, featured_contents, username)

                logger.info('emailed %s %s' % (username, email_address))


if __name__ == '__main__':
    f = file('t.json', 'rt')
    s = f.read()
    f.close()

    d = json.loads(s)

    if 0:
        t = ProcessDigest(d)
        t.start()
    else:
        import requests
        resp = requests.post('http://digests.506investorgroup.com:8081', json=d)
        print resp
