#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2

from Blog_Users import Blog_Users
from Blog_Posts import Blog_Posts
from Comments import Comments

from Handler import Handler
from LoginHandler import LoginHandler
from LogoutHandler import LogoutHandler
from SignUpHandler import SignUpHandler
from MainHandler import MainHandler
from UserPageHandler import UserPageHandler
from NewPost import NewPost
from DisableHandler import DisableHandler
from AdminPanel import AdminPanel
from SearchHandler import SearchHandler
from CommentsHandler import CommentsHandler


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
NUM_RE = r'((?:[0-9]+/?)*)'

app = webapp2.WSGIApplication([('/',             MainHandler),
                               ('/search'      + PAGE_RE, SearchHandler),
                               ('/login/?',      LoginHandler),
                               ('/logout/?',     LogoutHandler),
                               ('/signup/?',     SignUpHandler),
                               ('/user'        + PAGE_RE, UserPageHandler),
                               ('/adminpanel/?', AdminPanel),
                               ('/post/new/?',   NewPost),
                               ('/post'        + PAGE_RE, MainHandler),
                               ('/disable/'    + NUM_RE, DisableHandler),
                               ('/comments',     CommentsHandler),
                               (PAGE_RE,         MainHandler),
                                ], debug=True)
