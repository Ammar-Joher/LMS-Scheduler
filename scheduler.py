from datetime import datetime

import psycopg2
import sendgrid
from sendgrid.helpers.mail import *

img = 'https://i.ytimg.com/vi/xKxCowDNu-I/maxresdefault.jpg'
day_difference = 3


def send_notification_mail(cursor, manager_id, employee_name, manager_type):
    get_email_query = ""
    if manager_type == 'manager':
        get_email_query = "SELECT id, first_name, last_name, email FROM public.auth_user WHERE id=" + str(
            manager_id) + ";"
    elif manager_type == 'senior manager':
        get_email_query = "SELECT id, first_name, last_name, email FROM public.auth_user WHERE id=1;"

    sg = sendgrid.SendGridAPIClient('API-Key')

    cursor.execute(get_email_query)
    user_records = cursor.fetchall()

    email = None

    for row in user_records:
        print('Manger ID -> ', row[0])
        print('Manager First Name -> ', row[1])
        print('Manager Last Name -> ', row[2])
        print('Manager Email -> ', row[3])
        email = row[3]

    message = Mail(
        from_email='no-reply@chartercross.com',
        to_emails=email,
        subject='Leave Request Reminder',
        html_content='You Have Leave Requests Pending For ' + employee_name + '.'
    )
    try:
        print('EMAIL SENT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        sg.send(message)
        # print(response.status_code)
        # print(response.body)
        # print(response.headers)
    except Exception as e:
        print(e)


def get_unprocessed_leaves():
    try:
        # Connection to database
        connection = psycopg2.connect(user="postgres",
                                      password="1234",
                                      host="",
                                      port="5432",
                                      database="LMS")
        # database object
        cursor = connection.cursor()

        select_users_1 = 'SELECT id, status, employee_id, processed_by_id, last_notification_sent FROM ' \
                         'public."AnnualLeave_leaves" WHERE status=1 or status=2;'
        cursor.execute(select_users_1)
        user_records = cursor.fetchall()

        for row in user_records:
            leave_id = row[0]
            print('ID -> ', leave_id)
            print('Status -> ', row[1])
            user_id = row[2]
            print('Employee ID -> ', user_id)
            print('Processed By ID -> ', row[3])
            print('Last Time Notification Sent -> ', row[4])
            shutup = abs(row[4]-datetime.now().date())
            print('Days Difference ->', shutup.days)

            employee_name = get_employee(cursor, user_id)

            if row[1] == 1 and shutup.days >= day_difference:
                manager_id = get_manager(cursor, user_id)
                send_notification_mail(cursor, manager_id, employee_name, 'manager')
                update_last_sent_time(cursor, connection, leave_id)
            elif row[1] == 2 and shutup.days >= day_difference:
                manager_id = get_manager(cursor, user_id)
                send_notification_mail(cursor, manager_id, employee_name, 'senior manager')
                update_last_sent_time(cursor, connection, leave_id)

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)


def get_manager(cursor, user_id):
    get_manager_query = "SELECT id, manager_id, user_id FROM public.users_employee WHERE user_id=" + str(user_id) + ";"
    cursor.execute(get_manager_query)
    user_records = cursor.fetchall()

    for row in user_records:
        return row[1]


def get_employee(cursor, user_id):
    get_employee_query = "SELECT id, first_name, last_name, email FROM public.auth_user WHERE id=" + str(user_id) + ";"
    cursor.execute(get_employee_query)
    user_records = cursor.fetchall()

    for row in user_records:
        return row[1] + " " + row[2]


def update_last_sent_time(cursor, con, leave_id):
    update_last_sent_time_query = 'UPDATE public."AnnualLeave_leaves" SET last_notification_sent=now() ' \
                                  'WHERE id=' + str(leave_id) + ';'
    cursor.execute(update_last_sent_time_query)
    con.commit()


get_unprocessed_leaves()
