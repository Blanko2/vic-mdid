def is_mobile(request):
		mobile_uas = [
			'w3c ','acs-','alav','alca','amoi','audi','avan','benq','bird','blac',
			'blaz','brew','cell','cldc','cmd-','dang','doco','eric','hipt','inno',
			'ipaq','java','jigs','kddi','keji','leno','lg-c','lg-d','lg-g','lge-',
			'maui','maxo','midp','mits','mmef','mobi','mot-','moto','mwbp','nec-',
			'newt','noki','oper','palm','pana','pant','phil','play','port','prox',
			'qwap','sage','sams','sany','sch-','sec-','send','seri','sgh-','shar',
			'sie-','siem','smal','smar','sony','sph-','symb','t-mo','teli','tim-',
			'tosh','tsm-','upg1','upsi','vk-v','voda','wap-','wapa','wapi','wapp',
			'wapr','webc','winw','winw','xda','xda-',
		]
 
		mobile_ua_hints = [ 'SymbianOS', 'Opera Mini', 'iPhone' ]
		''' Super simple device detection, returns True for mobile devices '''
	 
		ua = request.META['HTTP_USER_AGENT'].lower()[0:4]
	 
		if (ua in mobile_uas):
			return True
		else:
			for hint in mobile_ua_hints:
				if request.META['HTTP_USER_AGENT'].find(hint) > 0:
					return True
	 	return False
