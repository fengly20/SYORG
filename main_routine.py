#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
@script name: main.py 
@author: Leyang Feng
@date last updated: 
@purpose: 
@note: 
@TODO:

"""

# -----------------------------------------------------------------
# 0. standard import
from __future__ import print_function
import httplib2
import os
from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools
import base64
import email
import re
import csv
import html2text

# -----------------------------------------------------------------
# 0.5. define scope and API key
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'

# -----------------------------------------------------------------
# 1. deal with credentials
home_dir = os.path.expanduser('~')
credential_dir = os.path.join(home_dir, '.credentials')
if not os.path.exists(credential_dir):
    os.makedirs(credential_dir)
credential_path = os.path.join(credential_dir, 'gmail-python-quickstart.json')

store = oauth2client.file.Storage(credential_path)
credentials = store.get()
if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
    credentials = tools.run_flow( flow, store )


#store = oauth2client.file.Storage( 'storage.json' )
#credentials = store.get()

#if not credentials or credentials.invalid:
#    flow = client.flow_from_clientsecrets( CLIENT_SECRET_FILE, SCOPES )
#    credentials = tools.run_flow( flow, store )

# -----------------------------------------------------------------
# 2. build a service gmail object

http = credentials.authorize( httplib2.Http() )
gmail = discovery.build( 'gmail', 'v1', http=http )

# -----------------------------------------------------------------
# 2.5. define user_id 
user_id = 'yfcui2009@gmail.com'

# -----------------------------------------------------------------
# 3. retrieve label_list
results = gmail.users().labels().list( userId = user_id ).execute()
labels = results.get('labels', [] )

if not labels:
    print('No labels found.')
else:
    user_label_list = [] # extract only user defined labels
    for label in labels:
        if label[ 'type' ] ==  'user':        
            user_label_list.append( label[ 'name' ] )  

label_list = user_label_list

#print( label_list )
del label_list[ 0 ]
del label_list[ 3 ]
# -----------------------------------------------------------------
# 4. retrieve threads under each label 

# empty list for later storage
summary_table = []

# looping through each label 
for label in label_list: 
    
    query_mess = 'label:'+ label 
    response = gmail.users().threads().list( userId = user_id,  q = query_mess ).execute()
    threads = []
    if 'threads' in response:
        threads.extend( response[ 'threads' ] )

    while 'nextPageToken' in response:
        page_token = response[ 'nextPageToken' ]
        response = gmail.users().threads().list( userId = user_id, q = query_mess, pageToken = page_token ).execute()
        threads.extend( response[ 'threads' ] )
      
    # ------------------------------------------------------
    # 5. retrieve thread data in each thread 
    for thread in threads: 
        tdata = gmail.users().threads().get( userId = user_id, id = thread[ 'id' ] ).execute()
        # only retrieve the first message in a thread      
        msg = tdata[ 'messages' ][ 0 ]
        msg_id = msg[ 'id' ]
     
        # ----------------------------------------------------
        # 6. retrieve the message using msg_id 
        message = gmail.users().messages().get(userId = user_id, id = msg_id, format = 'raw' ).execute()
        # transfer gmail message dictionary into string      
        msg_str = base64.urlsafe_b64decode( message[ 'raw' ].encode( 'ASCII' ) )
        # transfer message string into MIME class      
        mime_msg = email.message_from_string( msg_str )

        # ----------------------------------------------------
        # 7. walk through different parts in MIME class then extract the text part 
        for part in mime_msg.walk():
            if part.get_content_type() == 'text/html':
                email_html = part.get_payload()
                break
        
        # convert html to plain text 
        email_text = html2text.html2text( email_html )            
        # convert email_text form unicode to str
        email_text = str( email_text )        
        # split the whole string into lines  
        email_text = email_text.splitlines() 
    
        # extract date 
        for line in email_text:
            reg_results = re.search( r'^Date', line )
            if reg_results: 
                tag_line = line
                break
        
        msg_date = tag_line[ 6 : len( tag_line ) ]

        # extract the order number 
        reg_pat= 'confirmation number|order number|order #'
        for line in email_text:
            reg_results = re.search( reg_pat, line, re.I )
            if reg_results: 
                tag_line = line
                break
        if tag_line:
            line_parts = tag_line.split( )
            order_num = line_parts[ -1 ]
        else: 
            order_num = 'non-fetched'
        
        # extract the order total
        reg_pat = '^total|order total|total order|total amount'
        for line in email_text:
            reg_results = re.search( r'^total|total:', line, re.I )
            if reg_results: 
                tag_line = line
        if tag_line:
            line_parts = tag_line.split( )
            order_total = line_parts[ -1 ]
        else: 
            order_total = 'non-fetched'
        
        # summary line in dict
        summary_line = { 'label':str( label ), 'date':msg_date, 'order#':order_num, 'total':order_total }
        # summary line in list        
        #summary_line = [ label, msg_date, order_num, order_total ]        
        # append each summary_line to summary_table        
        summary_table.append( summary_line )                    
                
                
                
                
                
                
                
                
                
                
                
                