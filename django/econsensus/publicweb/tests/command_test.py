# pylint: disable=W0703
#         W0703 - Too general exception
#Test commands that have been added to manage.py
import poplib
from django.core import management, mail
from publicweb.tests.decision_test_case import EconsensusTestCase
from publicweb.tests import dummy_poplib
from publicweb.models import Decision, Feedback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.contrib.comments.models import Comment
from django.core import mail
from django.utils import timezone
from django.contrib.sites.models import Site
from django.contrib.contenttypes.models import ContentType


class CommandTest(EconsensusTestCase):

    poplib.POP3 = dummy_poplib.POP3
    poplib.POP3_SSL = dummy_poplib.POP3_SSL

    def test_process_email_new_proposal(self):
        #Tests that process_email picks up mails from mailbox
        #and creates objects in the db
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (self.betty, self.betty.email)),
                                      str('To: %s <%s@econsensus.com>' % (self.bettysorg.name, self.bettysorg.slug)),
                                      'Subject: Proposal gleda raspored',
                                      '',
                                      'Mnogi programi za stolno izdavatvo', ''], [''])

        try:
            management.call_command('process_email')
        except:
            self.fail("Exception was raised when processing legitimate email.")
        try:
            decision = Decision.objects.latest('id')
        except:
            self.fail("Email failed to appear in database as a decision.")
        self.assertEqual(decision.status, Decision.PROPOSAL_STATUS)
        
    def test_process_email_basic_feedback(self):
        #Tests that if [*] tag is in the header, a new feedback is created
        self.make_decision()
        count = Feedback.objects.count()
        email = getattr(mail, 'outbox')[-1]
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (email.to, email.to)),
                                      str('To: %s <%s>' % (email.from_email, email.from_email)),
                                      str('Subject: Re: %s' % email.subject),
                                      '',
                                      "This is a good idea", ''], [''])
        try:
            management.call_command('process_email')
        except:
            self.fail("Exception was raised when processing legitimate email.")

        feedback = Feedback.objects.latest('id')
        self.assertEqual(count+1, Feedback.objects.count())
        self.assertEqual(feedback.rating, Feedback.COMMENT_STATUS)
        self.assertEqual(feedback.description, "This is a good idea")

    def test_process_email_defined_feedback(self):
        #Tests that if a defined feedback type is passed it is transformed
        #into the rating field.
        self.make_decision()
        count = Feedback.objects.count()
        email = getattr(mail, 'outbox')[-1]
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (email.to, email.to)),
                                      str('To: %s <%s>' % (email.from_email, email.from_email)),
                                      str('Subject: Re: %s' % email.subject),
                                      '',
                                      "Danger: This is a bad idea", ''], [''])
        try:
            management.call_command('process_email')
        except:
            self.fail("Exception was raised when processing legitimate email.")

        feedback = Feedback.objects.latest('id')
        self.assertEqual(count+1, Feedback.objects.count())
        self.assertEqual(feedback.rating, Feedback.DANGER_STATUS)
        self.assertEqual(feedback.description, "This is a bad idea")

    def test_process_email_unrecognised_feedback(self):
        #Tests that if the user mistypes the feedback type it is ignored
        #and the feedback defaults to comment
        self.make_decision()
        count = Feedback.objects.count()
        email = getattr(mail, 'outbox')[-1]
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (email.to, email.to)),
                                      str('To: %s <%s>' % (email.from_email, email.from_email)),
                                      str('Subject: Re: %s' % email.subject),
                                      '',
                                      "Dager: This is a bad idea", ''], [''])
        try:
            management.call_command('process_email')
        except:
            self.fail("Exception was raised when processing legitimate email.")

        feedback = Feedback.objects.latest('id')
        self.assertEqual(count+1, Feedback.objects.count())
        self.assertEqual(feedback.rating, Feedback.COMMENT_STATUS)
        self.assertEqual(feedback.description, "This is a bad idea")

    def test_process_email_empty_feedback(self):
        #Tests that users can assign just the rating, leaving description blank
        #and the feedback defaults to comment
        self.make_decision()
        count = Feedback.objects.count()
        email = getattr(mail, 'outbox')[-1]
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (email.to, email.to)),
                                      str('To: %s <%s>' % (email.from_email, email.from_email)),
                                      str('Subject: Re: %s' % email.subject),
                                      '',
                                      "Danger:", ''], [''])
        try:
            management.call_command('process_email')
        except:
            self.fail("Exception was raised when processing legitimate email.")

        feedback = Feedback.objects.latest('id')
        self.assertEqual(count+1, Feedback.objects.count())
        self.assertEqual(feedback.rating, Feedback.DANGER_STATUS)
        self.assertEqual(feedback.description, "")

    def test_process_email_reply_to_feedback_with_comment(self):
        #Tests that a reply to a new feedback notification results in a new comment.
        comment_body = 'Comment description'
        decision = self.make_decision()
        feedback = self.make_feedback(decision=decision)
        count = Comment.objects.count()
        email = getattr(mail, 'outbox')[-1]
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (email.to, email.to)),
                                      str('To: %s <%s>' % (email.from_email, email.from_email)),
                                      str('Subject: Re: %s' % email.subject),
                                      '',
                                      comment_body, ''], [''])
        try:
            management.call_command('process_email')
        except:
            self.fail("Exception was raised when processing legitimate email.")
        self.assertEqual(count + 1, Comment.objects.count(), "New comment failed to appear in database")
        comment = Comment.objects.latest('id')
        self.assertEqual(comment.comment, comment_body)

    def test_process_email_reply_to_feedback_with_rating(self):
        '''
        User replies to a feedback email with rating appear as Feedback
        If a User replies to a feedback email with a rating then
        Feedback should be created against the original Decision
        '''
        decision = self.make_decision()
        first_feedback = self.make_feedback(decision=decision)
        email = getattr(mail, 'outbox')[-1]
        
        rating_str = Feedback.RATING_CHOICES[Feedback.QUESTION_STATUS][1]
        description = 'Some description'
        mail_body = str(rating_str.upper() +' : ' + description)
        
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (email.to, email.to)),
                                      str('To: %s <%s>' % (email.from_email, email.from_email)),
                                      str('Subject: Re: %s' % email.subject),
                                      '',
                                      mail_body, ''], [''])

        try:
            management.call_command('process_email')
        except:
            self.fail("Exception was raised when processing legitimate email.")

        new_feedback = Feedback.objects.latest('id')
        self.assertNotEqual(first_feedback.id, new_feedback.id)
        self.assertEqual(new_feedback.description, description)
        self.assertEqual(new_feedback.get_rating_display(), rating_str)
        

    def test_process_email_reply_to_comment_with_comment(self):
        #Tests that a reply to a new comment notification results in a new comment if no rating supplied.
        comment_body = 'Comment description'
        decision = self.make_decision()
        feedback = self.make_feedback(decision=decision)
        feedback_type = ContentType.objects.get(app_label="publicweb", model="feedback")
        self.make_comment(user=self.user,
                                    content_object=feedback, 
                                    object_pk=feedback.id,
                                    content_type=feedback_type,
                                    submit_date = timezone.now(),
                                    site = Site.objects.get_current())
        count = Comment.objects.count()
        email = getattr(mail, 'outbox')[-1]
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (email.to, email.to)),
                                      str('To: %s <%s>' % (email.from_email, email.from_email)),
                                      str('Subject: Re: %s' % email.subject),
                                      '',
                                      comment_body, ''], [''])
        try:
            management.call_command('process_email')
        except:
            self.fail("Exception was raised when processing legitimate email.")
        self.assertEqual(count + 1, Comment.objects.count(), "New comment failed to appear in database")
        comment = Comment.objects.latest('id')
        self.assertEqual(comment.comment, comment_body)
        

    def test_process_email_reply_to_comment_with_rating(self):
        '''
        User replies to a comment email with rating appears as Feedback
        If a User replies to a comment email with a rating then
        Feedback should be created against the original Decision
        '''
        decision = self.make_decision()
        first_feedback = self.make_feedback(decision=decision)
        feedback_type = ContentType.objects.get(app_label="publicweb", model="feedback")
        self.make_comment(user=self.user,
                                    content_object=first_feedback, 
                                    object_pk=first_feedback.id,
                                    content_type=feedback_type,
                                    submit_date = timezone.now(),
                                    site = Site.objects.get_current())
        email = getattr(mail, 'outbox')[-1]
        
        rating_str = Feedback.RATING_CHOICES[Feedback.QUESTION_STATUS][1]
        description = 'Some description'
        mail_body = str(rating_str.upper() +' : ' + description)
        
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (email.to, email.to)),
                                      str('To: %s <%s>' % (email.from_email, email.from_email)),
                                      str('Subject: Re: %s' % email.subject),
                                      '',
                                      mail_body, ''], [''])

        try:
            management.call_command('process_email')
        except:
            self.fail("Exception was raised when processing legitimate email.")

        new_feedback = Feedback.objects.latest('id')
        self.assertNotEqual(first_feedback.id, new_feedback.id)
        self.assertEqual(new_feedback.description, description)
        self.assertEqual(new_feedback.get_rating_display(), rating_str)


    def test_process_email_bad_content(self):
        initial_count = Decision.objects.count()
        #Test that an unknown email address is rejected.
        poplib.POP3.mailbox = ([''], ['From: Secret <youdont@knowme.com>',
                                      str('To: %s <%s@econsensus.com>' % (self.bettysorg.name, self.bettysorg.slug)),
                                      'Subject: gleda Issue #54',
                                      '',
                                      'Mnogi programi za stolno izdavatvo', ''], [''])
        self.assertFalse(Decision.objects.count() - initial_count)
        
        #Test that a corrupt from field is rejected.
        poplib.POP3.mailbox = ([''], ['From: Donald <spam>',
                                      str('To: %s <%s@econsensus.com>' % (self.bettysorg.name, self.bettysorg.slug)),
                                      'Subject: Re: [8] New decision',
                                      '',
                                      'Mnogi programi za stolno izdavatvo', ''], [''])
        self.assertFalse(Decision.objects.count() - initial_count)

    def test_email_sent_out_on_email_decision(self):
        poplib.POP3.mailbox = ([''], [str('From: %s <%s>' % (self.betty, self.betty.email)),
                                      str('To: self.bettysorg.name <%s@econsensus.com>' % self.bettysorg.slug),
                                      'Subject: Proposal gleda raspored',
                                      '',
                                      'Mnogi programi za stolno izdavatvo', ''], [''])
        try:
            management.call_command('process_email')
        except Exception, e:
            self.fail("Exception: %s" % e)
        
        outbox = getattr(mail, 'outbox')
        self.assertTrue(outbox)

    def test_email_replies_are_chevron_stripped(self):
        """
        Replies should have any quotes, marked with '>' removed.
        """
        payload = """
        Unquoted text.
        >
        >Some quoted text.
        >
        """
        msg = MIMEText(payload)
        msg['Subject'] = 'Proposal gleda raspored'
        
        msg['From'] = self.betty.email
        msg['To'] = '%s@econsensus.com>' % self.bettysorg.slug
     
        poplib.POP3.mailbox = ([''], [msg.as_string()], [''])
        try:
            management.call_command('process_email')
        except Exception, e:
            self.fail("Exception: %s" % e)
        
        try:
            decision = Decision.objects.latest('id')
        except:
            self.fail("Email failed to appear in database as a decision.")
        self.assertNotIn("Some quoted text.", decision.description)
        self.assertIn("Unquoted text.", decision.description)
        
    def test_email_replies_are_quote_header_stripped(self):
        """
        Replies should have the 'header' of a quote removed.
        Ie 'On Thursday Tom wrote:'
        """
        payload = """
        Proposal XYZ
        On 24/07/12 18:14, Mark Skipper wrote:
        >
        >Some quoted text.
        >
        """
        msg = MIMEText(payload)
        msg['Subject'] = 'Proposal gleda raspored'
        msg['From'] = self.betty.email
        msg['To'] = '%s@econsensus.com>' % self.bettysorg.slug
        poplib.POP3.mailbox = ([''], [msg.as_string()], [''])
        try:
            management.call_command('process_email')
        except Exception, e:
            self.fail("Exception: %s" % e)
        
        try:
            decision = Decision.objects.latest('id')
        except:
            self.fail("Email failed to appear in database as a decision.")
        self.assertNotIn("On 24/07/12 18:14, Mark Skipper wrote:", decision.description)
        self.assertIn("Proposal XYZ", decision.description)
    
    def test_multipart_mail(self):
        """Ensure that the command can process multipart emails."""
        msg = MIMEMultipart()
        msg['Subject'] = 'Proposal gleda raspored'
        msg['From'] = self.betty.email
        msg['To'] = '%s@econsensus.com>' % self.bettysorg.slug
        payload = "Sample payload"
        sub_msg = MIMEText(payload)
        msg.attach(sub_msg)
        payload = "Another payload"
        sub_msg = MIMEText(payload)
        msg.attach(sub_msg)
        poplib.POP3.mailbox = ([''], [msg.as_string()], [''])
        try:
            management.call_command('process_email')
        except Exception, e:
            self.fail("Exception: %s" % e)
        
        try:
            Decision.objects.latest('id')
        except:
            self.fail("Email failed to appear in database as a decision.")
