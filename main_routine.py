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

print( label_list )
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
            
        # extract desired info using regular expression     
        email_html = email_html.splitlines() 
        
        # extract date 
        #for line in email_text:
        for line in email_html:
            #reg_results = re.search( r'Date', line, re.I )            
            reg_results = re.search( r'Date.*<', line )
            if reg_results: 
                break
        #msg_date = tag_line[ 6 : len( tag_line ) ]       
        msg_date = reg_results.group()[ 6 : len( reg_results.group() ) - 1 ]
        del reg_results
        
        # extract the order number 
        reg_pat= 'confirmation number|order number|order #'
        #for i in range( 0, len( email_text ) ):
        for i in range( 0, len( email_html ) ): 
            #reg_results = re.search( reg_pat, email_text[ i ], re.I )
            reg_results = re.search( reg_pat, email_html[ i ], re.I )
            if reg_results: 
                tag_line = email_html[ i ]
                #tag_line = email_text[ i ]
                break
        if 'tag_line' in globals():
            reg_results = re.search( r'\d', tag_line )
            if reg_results:
                line_parts = tag_line.split()
                order_num = line_parts[ -1 ]
            else:
                tag_line = email_html[ i+1 ]
                order_num = tag_line
            del tag_line 
        else: 
            order_num = 'non-fetched'
        # cleaning of the order_num
        order_num = re.sub( r'\#|\*', "", order_num)
        del reg_results
                 
        # extract the order total
        #reg_pat = 'order total|total order|^total|total amount|card to charge.|total charge'
        reg_pat = '>.*' + 'order total|total order|^total|total amount|card to charge.|total charge' + '.*<'
        #reg_pat = r'>.*total charge.*<'        
        for i in range( 0, len( email_html ) ):
            reg_results = re.search( reg_pat, email_html[ i ], re.I )
            if reg_results: 
                break
        tag_line = reg_results.group() 
        if 'tag_line' in globals():
            if re.search( r'\d', tag_line ):
                order_total = re.search( r'\d', tag_line ).group()
            else: 
                reg_results = re.search( r'>[0-9].*[0-9]<', email_html[ i+1 ] )
                order_total = reg_results.group() 
        else: 
            order_total = 'non-fetched'     
        del tag_line 
        del reg_results
        # cleaning of the order_total
        order_total = re.sub( r'\$|\*|>|<', "", order_total)
        
        # summary line in dict style
        #summary_line = { 'label':str( label ), 'date':msg_date, 'order#':order_num, 'total':order_total }
        # summary line in list style       
        summary_line = [ label, msg_date, order_num, order_total ]        
        # append each summary_line to summary_table        
        summary_table.append( summary_line )      


with open( "preview.csv", "wb" ) as myfile:
    writer = csv.writer( myfile )
    writer.writerow(['label', 'date', 'order#', 'total' ] )
    writer.writerows( summary_table )


                
                
                
                
                
                
                
                
                
                
                