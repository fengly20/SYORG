#!/usr/bin/env python

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
user_id = 'phly.figlio@gmail.com'

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

# -----------------------------------------------------------------
# 4. retrieve threads under each label 
for label in label_list: 
    
    query_mess = 'label:'+ label 
    response = gmail.users().threads().list( userId = user_id,  q = query_mess ).execute()
    threads = []
    if 'threads' in response:
        threads.extend(response['threads'])

    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        esponse = gmail.users().threads().list(userId=user_id, q = query_mess, pageToken=page_token).execute()
        threads.extend(response['threads'])
      
    # ------------------------------------------------------
    # 5. retrieve thread data in each thread 
    for thread in threads: 
        tdata = gmail.users().threads().get( userId = user_id, id = thread[ 'id' ] ).execute()
        # only retrieve the first message in a thread      
        msg = tdata[ 'messages' ][ 0 ]
        msg_id = msg[ 'id' ]
      
        msg = msg[ 'payload' ]
        for header in msg[ 'headers' ]:
            if header[ 'name' ] == 'Date':
                msg_date = header[ 'value' ]
                break
      
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
            if part.get_content_type() == 'text/plain':
                mytext = part.get_payload()
                break
      
        for line in mytext: 
            line = line.rstrip()
            s = re.findall(r'order(.*)', line, re.I )  
            print( s )            
            #if re.search('order', line, re.I ):
            #    print ( line )
          
          