from cgitb import lookup
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics, status
from .serializers import RoomSerializer, CreateRoomSerializer
from .models import Room
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse

# Create your views here.

# Create Room
class RoomView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

# Get Room

class GetRoomView(APIView):
    serializar_class = RoomSerializer
    lookup_url_kwarg = 'code'

    def get(self, request, format=None):
        print(request.GET)
        code = request.GET.get(self.lookup_url_kwarg)
        
        if code != None:
            room = Room.objects.filter(code=code)
            if len(room) > 0:
                data = RoomSerializer(room[0]).data
                data['is_host'] = self.request.session.session_key == room[0].host
                
                return Response(data, status=status.HTTP_200_OK)
            
            return Response({'Room Not Found': 'Invalid Room  Code.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'Bad Request': 'Code paramater not found in request'}, status=status.HTTP_400_BAD_REQUEST)

# Join Room
class JoinRoomView(APIView):
    lookup_url_kwarg = 'code'

    def post(self, request, format=None):
        # Validamos que exista la session
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
        
        code = request.data.get(self.lookup_url_kwarg)
        if code != None :
            room_result = Room.objects.filter(code=code)
            if len(room_result) > 0:
                room = room_result[0]
                self.request.session['room_code'] = code

                return Response({'message': 'Room Joiner..!'}, status=status.HTTP_200_OK)

                return Response({'Bad Request': 'Invalid Room Code..!'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'Bad Request': 'Invalid post data, did not find a code key'}, status=status.HTTP_400_BAD_REQUEST)


# Create Room view
class CreateRoomView(APIView):
    serializer_class = CreateRoomSerializer
    
    def post(self, request, format=None):
        # Validamos que exista la session
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

        # Obtenemos la data de la vista 
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            guest_can_pause = serializer.data.get('guest_can_pause')
            votes_to_skip = serializer.data.get('votes_to_skip')
            host = self.request.session.session_key
            queryset = Room.objects.filter(host=host)
            
            if queryset.exists():
                room = queryset[0]
                room.guest_can_pause = guest_can_pause
                room.votes_to_skip = votes_to_skip
                room.save(update_fields=['guest_can_pause', 'votes_to_skip'])
                self.request.session['room_code'] = room.code

                return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
            
            else:
                room = Room(host=host, guest_can_pause=guest_can_pause, votes_to_skip=votes_to_skip)
                self.request.session['room_code'] = room.code
                room.save()
                self.request.session['room_code'] = room.code
                
                return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
        
        return Response({'Bad Request': 'Invalid data...'}, status=status.HTTP_400_BAD_REQUEST)


# User in Room
class UserInRoom(APIView):
    def get(self, request, format=None):
        # Validamos que exista la session
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()

        data = {
            'code': self.request.session.get('room_code'),
        }

        return JsonResponse(data, status=status.HTTP_200_OK)

# Leave Room
class LeaveRoom(APIView):
    def post(self, request, format=None):
        print(self.request)
        if 'room_code' in self.request.session:
            self.request.session.pop('room_code')
            host_id = self.request.session.session_key
            room_results = Room.objects.filter(host=host_id)
            if len(room_results) > 0:
                room = room_results[0]
                room.delete()

        return Response({'Message':'Success'}, status=status.HTTP_200_OK)