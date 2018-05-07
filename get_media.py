from groupy import Client
import boto3
import logging, optparse, os, urllib.request, sys

from credentials import *

# handle SIGINT, SIGTERM
def signal_handler(signal, frame):
	sys.exit(0)

# find the group that matches the gm_group_id
def find_group(client, id):
	groups = list(client.groups.list_all())

	for group in groups:
		if group.id == id:
			return group
	return false

# retrieve attachment data from a specified group
def retrieve_attachments(client, group):
	retrieved_attachments = []

	for message in group.messages.list_all():
		for attachment in message.attachments:
			retrieved_attachments.append({
				'id'		:	message.id,
				'createdat'	:	str(message.created_at),
				'url'		:	''
			})

			if attachment.data['type'] == 'image':
				if attachment.data['source_url'] != None:
					retrieved_attachments[len(retrieved_attachments) - 1]['url'] = attachment.data['source_url']
				else:
					retrieved_attachments[len(retrieved_attachments) - 1]['url'] = attachment.data['url']
			elif attachment.data['type'] == 'video':
				retrieved_attachments[len(retrieved_attachments) - 1]['url'] = attachment.data['url']

	logging.debug(retrieved_attachments)
	logging.info("%d attachments found in this group" % len(retrieved_attachments))

	return retrieved_attachments

def main():
	# configure the argument options parser for the script
	parser = optparse.OptionParser()
	parser.add_option('--debug', action="store_true", dest="debug", help="debug output", default=False)
	options, args = parser.parse_args()

	if options.debug == True:
		logging.basicConfig(level=logging.DEBUG)
	else:
		logging.basicConfig(level=logging.INFO)

	logging.info('Started')

	# configure client for groupy
	client = Client.from_token(groupme_token)

	# set up dynamodb
	#dynamodb = boto3.setup_default_session(region_name='us-east-1')
	#dynamodb = boto3.resource('dynamodb')

	# select the specific group
	try:
		group = find_group(client, gm_group_id)
		logging.info('Group selected (%s)' % gm_group_id)
	except:
		logging.error('Unable to find group')

	# retrieve attachment data from the group
	retrieved_attachments = []
	retrieved_attachments = retrieve_attachments(client, group)

	# create a subdirectory
	if not os.path.exists('dl'):
		os.mkdir('dl')

	logging.info("Starting download of all attachments...")

	# format the filenames of the attachments and proceed to downloading
	for attachment in retrieved_attachments:
		jpeg_ext = attachment['url'].rfind('.jpeg.')	# check for .jpeg
		png_ext = attachment['url'].rfind('.png.')		# check for .png
		backslash = attachment['url'].rfind('/')		# find last backslash

		# JPEG extension
		if jpeg_ext != -1:
			file_hash = attachment['url'][jpeg_ext + 6:]
			filename = file_hash + '.' + attachment['url'][backslash + 1:jpeg_ext + 5]
		# PNG extension
		elif png_ext != -1:
			file_hash = attachment['url'][png_ext + 5:]
			filename = file_hash + '.' + attachment['url'][backslash + 1:png_ext + 4]
		# all others
		else:
			filename = attachment['url'][backslash + 1:]

		try:
			logging.info('Downloading: %s' % attachment['url'])

			with open('dl/' + filename, 'wb') as f:
				f.write(urllib.request.urlopen(attachment['url']).read())
				f.close()

			logging.info('Saved to: %s' % filename)
		except:
			logging.error('Unable to download: %s' % attachment['url'])

if __name__ == "__main__":
	import signal

	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)
	
	main()