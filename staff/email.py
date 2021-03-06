import settings
import mailchimp
import traceback

from datetime import datetime, time, date, timedelta
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.core.mail import send_mail, EmailMessage
from models import Member, DailyLog, SentEmailLog

def send_introduction(user):
	site = Site.objects.get_current()
	subject = "%s: Introduction to Nadine" % (site.name)
	message = render_to_string('email/introduction.txt', {'user':user, 'site':site})
	send_quietly(user.email, subject, message)
	subscribe_to_newsletter(user)

def subscribe_to_newsletter(user):
	if settings.MAILCHIMP_NEWSLETTER_KEY:
		try:
			newsletter = mailchimp.utils.get_connection().get_list_by_id(settings.MAILCHIMP_NEWSLETTER_KEY)
			newsletter.subscribe(user.email, {'EMAIL':user.email, 'FNAME':user.first_name, 'LNAME':user.last_name})
		except:
			pass

def send_new_membership(user):
	site = Site.objects.get_current()
	membership = user.profile.last_membership()
	subject = "%s: New %s Membership" % (site.name, membership.membership_plan.name)
	message = render_to_string('email/new_membership.txt', {'user':user, 'membership':membership, 'site':site})
	send(user.email, subject, message)
	announce_new_membership(user)

def send_first_day_checkin(user):
	site = Site.objects.get_current()
	subject = "%s: How was your first day?" % (site.name)
	message = render_to_string('email/first_day.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_exit_survey(user):
	site = Site.objects.get_current()
	subject = "%s: Exit Survey" % (site.name)
	message = render_to_string('email/exit_survey.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_member_survey(user):
	site = Site.objects.get_current()
	subject = "%s: Coworking Survey" % (site.name)
	message = render_to_string('email/member_survey.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_no_return_checkin(user):
	site = Site.objects.get_current()
	subject = "%s: Checking In" % (site.name)
	message = render_to_string('email/no_return.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_invalid_billing(user):
	site = Site.objects.get_current()
	subject = "%s: Billing Problem" % (site.name)
	message = render_to_string('email/invalid_billing.txt', {'user':user, 'site':site})
	send(user.email, subject, message)

def send_user_notifications(user, target):
	site = Site.objects.get_current()
	subject = "%s: %s is here!" % (site.name, target.get_full_name())
	message = render_to_string('email/user_notification.txt', {'user':user, 'target':target, 'site':site})
	send(user.email, subject, message)
		
def announce_new_user(user):
	subject = "New User - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \t%s just signed in for the first time! %s" % (user.get_full_name(), team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_new_membership(user):
	membership = user.profile.last_membership()
	subject = "New %s: %s" % (membership.membership_plan.name, user.get_full_name())
	message = "Team,\r\n\r\n \t%s has a new %s membership! %s" % (user.get_full_name(), membership.membership_plan.name, team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_member_checkin(user):
	membership = user.profile.last_membership()
	subject = "Member Check-in - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \t%s has been a %s member for almost a month!  Someone go see how they are doing. %s" % (user.get_full_name(), membership.membership_plan.name, team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_need_photo(user):
	subject = "Photo Opportunity - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \t%s just signed in and we don't have a photo of them yet. %s" % (user.get_full_name(), team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def announce_bad_email(user):
	subject = "Email Problem - %s" % (user.get_full_name())
	message = "Team,\r\n\r\n \tWe had a problem sending the introduction email to '%s'. %s" % (user.email, team_signature(user))
	send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)

def team_signature(user):
	site = Site.objects.get_current()
	return render_to_string('email/team_email_signature.txt', {'user':user, 'site':site})

def send(recipient, subject, message):
	send_email(recipient, subject, message, False)

def send_quietly(recipient, subject, message):
	send_email(recipient, subject, message, True)

def send_email(recipient, subject, message, fail_silently):
	# A little safety net when debugging
	if settings.DEBUG:
		recipient = settings.EMAIL_ADDRESS

	note = None
	success = False
	try:
		msg = EmailMessage(subject, message, settings.EMAIL_ADDRESS, [recipient])
		#msg.content_subtype = "html"  # Main content is now text/html
		msg.send()
		success = True
	except:
		note = traceback.format_exc()
		if fail_silently:
			pass
		raise
	finally:
		member = None
		try:
			members = Member.objects.filter(user__email=recipient)
			if len(members) == 1:
				member = members[0]
		except:
			pass
		try:
			log = SentEmailLog(member=member, recipient=recipient, subject=subject, success=success)
			if note:
				log.note = note
			log.save()
		except:
			pass
