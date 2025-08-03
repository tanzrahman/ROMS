from django.shortcuts import redirect

from manpower.models import IPWhitelist
from django.http import HttpResponse
from task_management import ipcalc
class IPFilterMiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):

        response = self.get_response(request)

        ip = request.META['REMOTE_ADDR']

        print("conn_req_ip: ",ip)
        if(ip=='127.0.0.1'):
            # if (request.user.is_anonymous):
            #     if(request.path != "/user/signup" and request.path != "/login/" and request.path != "/"):
            #         return HttpResponse('Unauthorized Access: Login Required', status=401)
            return response
        if(ip.find("192.168.30")!=-1):
            # if (request.user.is_anonymous):
            #     if(request.path != "/user/signup" and request.path != "/login/" and request.path != "/"):
            #         return HttpResponse('Unauthorized Access: Login Required', status=401)
            return response
        if (ip.find("172.30.3") != -1):
            # if (request.user.is_anonymous):
            #     if(request.path != "/user/signup" and request.path != "/login/" and request.path != "/"):
            #         return HttpResponse('Unauthorized Access: Login Required', status=401)
            return response

        version = '4'
        seperator ='.'
        if(ip.find(':')!=-1):
            version = '6'
            seperator = ':'

        segments = ip.split(seperator)
        first_two_segments = segments[0]+seperator+segments[1]

        close_match = IPWhitelist.objects.filter(version=version,ip_address__istartswith=first_two_segments)
        if (close_match.count() < 1):
            print("unauthorized_conn_req_ip: ", ip)
            return HttpResponse('Unauthorized Access', status=401)

        valid_ip = False
        for each in close_match:
            network = each.ip_address+"/"+str(each.subnet)
            if(ip in ipcalc.Network(network) ):
                valid_ip = True
                break

        if(not valid_ip):
            return HttpResponse('Unauthorized Access', status=401)


        # if(request.user.is_anonymous):
        #     if(request.path != "/user/signup" and request.path != "/login/" and request.path != "/"):
        #         return HttpResponse('Unauthorized Access: Login Required', status=401)
        return response