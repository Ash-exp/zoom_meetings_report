import os
import sys
import json
import csv
import requests
from datetime import datetime
from datetime import timedelta

class Utils:
	ZOOM_REPORT_HEADER = ["HOST", "EMAIL", "ACTUAL SESSIONS", "BLANK SESSIONS", "TOTAL ACTUAL SESSIONS"]

	def __init__(self):
		self.load_config()


	def load_config(self):
		with open(os.path.abspath("config.json")) as json_data_file:
			data = json.load(json_data_file)

		self.zoom_token = data['zoom-token']
		self.report_mailer = data["report-mailer"]

	def get_record_row(self, record):
		row = []
		for record_name in self.ZOOM_REPORT_HEADER:
			row.append(record[record_name.lower().replace(' ','_')])
		return row

	def save_csv(self, fileobject, filename):
		print('\n'+' Saving report {filename} '.format(filename=filename).center(100,':'))

		file_exists = os.path.isfile(filename)
		with open(os.path.abspath(filename), 'w', newline='') as f: #'a'
			writer = csv.writer(f)
			#if not file_exists:
			writer.writerow(self.ZOOM_REPORT_HEADER)

			for record in fileobject:
				writer.writerow(self.get_record_row(record))


	def get_zoom_meetings(self, start_date, end_date):
		print(' Getting meetings list '.center(100,':'))

		url = "https://api.zoom.us/v2/metrics/meetings"
		query = {"page_size":"100"}
		headers = {'Authorization': 'Bearer '+self.zoom_token}

		end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
		meetings_list = []
		emails_list = []

		from_date = datetime.strptime(start_date, '%Y-%m-%d').date()  #date(2020, 01, 01)
		to_date = from_date + timedelta(days=30)
		if to_date > end_date:
			to_date = end_date

		while to_date < end_date+timedelta(days=1):
			query["from"] = str(from_date)
			query["to"] = str(to_date)

			print(' [{start_date}] - [{end_date}] '.format(start_date=start_date, end_date=end_date).center(100,':'))
			# print(' ['+str(from_date)+'] - ['+str(to_date)+'] ')
			counter = 0
			while True:
				counter += 1
				query["type"] = "pastOne"
				response = requests.request("GET", url, headers=headers, params=query)
				json_response = json.loads(response.content)
				print(len(json_response['meetings']))
				
				if json_response['total_records'] > 0:
					for meeting in json_response['meetings']:
						if meeting['email'] in emails_list:
							for record in meetings_list:
								if meeting['email'] == record['email']:
									record['blank_sessions'] += 1
									record['total_actual_sessions'] += 1
						else:
							item = {}
							emails_list.append(meeting['email'])
							item['host'] = meeting['host']
							item['email'] = meeting['email']
							item['actual_sessions'] = 0
							item['blank_sessions'] = 1
							item['total_actual_sessions'] = 1
							meetings_list.append(item)

				if json_response["next_page_token"] == '':
					break
				else: query["next_page_token"] = json_response["next_page_token"]

			# print(meetings_list)
			del query["next_page_token"]
			counter = 0
			while True:
				query["type"] = "past"
				counter += 1
				response = requests.request("GET", url, headers=headers, params=query)
				json_response = json.loads(response.content)
				print(len(json_response['meetings']))
				
				if json_response['total_records'] > 0:
					for meeting in json_response['meetings']:
						if meeting['email'] in emails_list:
							for record in meetings_list:
								if meeting['email'] == record['email']:
									record['actual_sessions'] += 1
									record['total_actual_sessions'] += 1
						else:
							item = {}
							emails_list.append(meeting['email'])
							item['host'] = meeting['host']
							item['email'] = meeting['email']
							item['actual_sessions'] = 1
							item['blank_sessions'] = 0
							item['total_actual_sessions'] = 1
							meetings_list.append(item)

				if json_response["next_page_token"] == '':
					break
				else: query["next_page_token"] = json_response["next_page_token"]

			from_date = to_date + timedelta(days=1)
			to_date = to_date + timedelta(days=30)

			if (to_date > end_date) and ((to_date - timedelta(days=30)) != end_date):
				to_date = end_date
		
		return meetings_list


	def get_zoom_attendace(self, start_date):
		print(' Getting meetings list '.center(100,':'))

		url = "https://api.zoom.us/v2/metrics/meetings"
		query = {"page_size":"100"}
		headers = {'Authorization': 'Bearer '+self.zoom_token}

		end_date = datetime.strptime(start_date, '%Y-%m-%d').date()
		meetings_list = []
		emails_list = []

		from_date = datetime.strptime(start_date, '%Y-%m-%d').date()  #date(2020, 01, 01)

		query["from"] = str(from_date)
		query["to"] = str(from_date)

		print(' [{start_date}] - [{end_date}] '.format(start_date=start_date, end_date=end_date).center(100,':'))
		# print(' ['+str(from_date)+'] - ['+str(to_date)+'] ')
		
		while True:
			query["type"] = "past"

			response = requests.request("GET", url, headers=headers, params=query)
			json_response = json.loads(response.content)
			print(len(json_response['meetings']))
			
			if json_response['total_records'] > 0:
				for meeting in json_response['meetings']:
					if '@' in meeting['topic'] and '(' in meeting['topic']:
						if meeting['email'] in emails_list:
							for record in meetings_list:
								if meeting['email'] == record['email']:
									record['actual_sessions'] += (meeting['topic'].split('(')[0]).strip()+', '
									record['total_actual_sessions'] += 1
						else:
							item = {}
							emails_list.append(meeting['email'])
							item['host'] = meeting['host']
							item['email'] = meeting['email']
							item['actual_sessions'] = (meeting['topic'].split('(')[0]).strip()+', '
							item['blank_sessions'] = ''
							item['total_actual_sessions'] = 1
							meetings_list.append(item)

			if json_response["next_page_token"] == '':
				break
			else: query["next_page_token"] = json_response["next_page_token"]
		
		# print(meetings_list)
		if "next_page_token" in query.keys() :
			del query["next_page_token"]

		while True:
			query["type"] = "pastOne"
			response = requests.request("GET", url, headers=headers, params=query)
			json_response = json.loads(response.content)
			print(len(json_response['meetings']))
			
			if json_response['total_records'] > 0:
				for meeting in json_response['meetings']:
					if '@' in meeting['topic'] and '(' in meeting['topic']:
						if meeting['email'] in emails_list:
							for record in meetings_list:
								if meeting['email'] == record['email']:
									if not (meeting['topic'].split('(')[0]).strip()+', ' in record['actual_sessions']:
										record['blank_sessions'] += (meeting['topic'].split('(')[0]).strip()+', '
						else:
							item = {}
							emails_list.append(meeting['email'])
							item['host'] = meeting['host']
							item['email'] = meeting['email']
							item['actual_sessions'] = ''
							item['blank_sessions'] = (meeting['topic'].split('(')[0]).strip()+', '
							item['total_actual_sessions'] = 0
							meetings_list.append(item)

			if json_response["next_page_token"] == '':
				break
			else: query["next_page_token"] = json_response["next_page_token"]

		print(emails_list)
		return meetings_list



if __name__ == "__main__":
	date = "2021-08-18" 
	start_date = "2021-08-01" 
	end_date = "2021-08-08" 
	utils = Utils()
	# files = utils.get_zoom_meetings(start_date, end_date)
	# utils.save_csv(files, "Zoom_Report_file.csv")
	files = utils.get_zoom_attendace(date)
	utils.save_csv(files, "Zoom_Attandance_file.csv")