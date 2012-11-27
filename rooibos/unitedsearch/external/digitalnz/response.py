# Copyright (C) 2009 Mark A. Matienzo
#
# This file is part of the digitalnz Python module.
#
# digitalnz is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# digitalnz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with digitalnz.  If not, see <http://www.gnu.org/licenses/>.

# response.py - response classes


try:
    import json                 # Python >= 2.6
except ImportError:
    import simplejson as json   # otherwise require simplejson
    

class DigitalNZResponse(object):
    """docstring for DigitalNZResponse"""
    def __init__(self, request, data):
        super(DigitalNZResponse, self).__init__()
        self.format = request.format
        if request.parsing is True and request.format == 'json':
            self.data = json.loads(data)
            self.parsed = True
        else:
            self.data = data
            self.parsed = False
