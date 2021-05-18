from django.shortcuts import redirect
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveAPIView
from rest_framework.views import APIView
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from openedx.core.lib.api.authentication import BearerAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated
from openedx.core.lib.api.permissions import IsStaffOrOwner
from django.utils import timezone
from student.models import CourseEnrollment
from .models import Note, NoteImages
from .serializers import MyNoteImageSerializer, NoteSerializer, MyNoteSerializer

from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from openedx.core.djangoapps.user_api.accounts.permissions import CanRetireUser

from django.contrib.auth.models import User
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment
from edx_rest_framework_extensions.permissions import NotJwtRestrictedApplication
from PIL import Image
from io import BytesIO
from django.core.files.storage import FileSystemStorage
from openedx.core.djangoapps.profile_images.images import validate_uploaded_image
#from .exceptions import ImageValidationError
from six import text_type
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser, FileUploadParser

from django.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey
from courseware.courses import get_course_with_access
import logging



log = logging.getLogger(__name__)

class ApiKeyPermissionMixIn(object):
    """
    This mixin is used to provide a convenience function for doing individual permission checks
    for the presence of API keys.
    """

    def has_api_key_permissions(self, request):
        """
        Checks to see if the request was made by a server with an API key.

        Args:
            request (Request): the request being made into the view

        Return:
            True if the request has been made with a valid API key
            False otherwise
        """
        return ApiKeyHeaderPermission().has_permission(request, self)
      
class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

class MyNoteListView(ListAPIView):
    authentication_classes = (BearerAuthentication, )
    permission_classes = (IsAuthenticated, )
    queryset = Note.objects.all()
    serializer_class = MyNoteSerializer

    def get(self, request, course_id):
        try:
            student_id = request.user.id
            notes = Note.objects.filter(student_id=student_id, course_id=course_id)
            results = [ob.as_json() for ob in notes]
            data = []
            for note in results:
                note_id = note['id']
                if NoteImages.objects.filter(note_id=note_id).exists():
                    note_images = NoteImages.objects.filter(note_id=note_id)
                    note_image = MyNoteImageSerializer(note_images, many=True, context={"request": request}).data
                    data.append({'note': note, 'note_images': note_image})
                else:
                    data.append({'note': note})                    
        except Note.DoesNotExist:
            return Response({'error': 'Not found.', 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"result": data, "status_code": status.HTTP_200_OK, "message": "Own Notes.", "status": True}, status=status.HTTP_200_OK) 


class PeerNotesView(RetrieveAPIView):
    authentication_classes = (JwtAuthentication, BearerAuthentication)
    permission_classes = (IsAuthenticated, )

    def get(self, request, course_id):
        try:
            notes = Note.objects.filter(is_public=True, course_id=course_id)
            results = [ob.as_json() for ob in notes]
            data = []
            for note in results:
                note_id = note['id']
                if NoteImages.objects.filter(note_id=note_id).exists():
                    note_images = NoteImages.objects.filter(note_id=note_id)
                    note_image = MyNoteImageSerializer(note_images, many=True, context={"request": request}).data
                    data.append({'note': note, 'note_images': note_image})
                else:
                    data.append({'note': note}) 
        except Note.DoesNotExist:
            return Response({'error': 'Not found.', 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"result": data, "status_code": status.HTTP_200_OK, "message": "Peer Notes.", "status": True}, status=status.HTTP_200_OK) 
        


class MyNoteDeleteView(APIView):
    authentication_classes = (BearerAuthentication, JwtAuthentication,)
    permission_classes = (IsAuthenticated, NotJwtRestrictedApplication,)
    queryset = Note.objects.all()

    def delete(self, request, id):
        try:
            student_id = request.user.id
            data =[]
            note = Note.objects.get(id=id, student_id=student_id)
            note_id = note.id
            note_images = NoteImages.objects.filter(note_id=note_id)
            note_image = MyNoteImageSerializer(note_images, many=True, context={"request": request}).data
            note.delete()
            note_images.delete()
            data.append({'note': note.as_json(), 'note_images': note_image})
        except:
            return Response({'error': "Not Found!!", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"result": data, "status_code": status.HTTP_200_OK, "message": "Note deleted successfully.", "status": True}, status=status.HTTP_200_OK) 

class MyNoteImageDeleteView(APIView):
    authentication_classes = (BearerAuthentication, JwtAuthentication,)
    permission_classes = (IsAuthenticated, NotJwtRestrictedApplication,)
    queryset = Note.objects.all()

    def delete(self, request, id):
        try:
            note_image = NoteImages.objects.get(id=id)            
            noteImage = MyNoteImageSerializer(note_image, context={"request": request}).data
            note_image.delete()
        except:
            return Response({'error': "Not Found!!", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"result": noteImage, "status_code": status.HTTP_200_OK, "message": "NoteImage deleted successfully.", "status": True}, status=status.HTTP_200_OK) 

def resize_image(image):
    basewidth = 300
    # baseheight = 560
    img = Image.open(image)
    
    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    
    # hpercent = (baseheight / float(img.size[1]))
    # wsize = int((float(img.size[0]) * float(hpercent)))
    
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    # w, h = img.size
    # img = img.resize((w/2, h/2))
    image_file = BytesIO()
    
    img.save(image_file, 'JPEG', quality=90)
    image.file = image_file
    return image

class MyNoteUpdateView(APIView):
    authentication_classes = (BearerAuthentication, )
    permission_classes = (IsAuthenticated, )
    queryset = Note.objects.all()

    def put(self, request, id):
        try:
            student_id = request.user.id
            note = Note.objects.get(id=id, student_id=student_id)
            user = User.objects.get(id=student_id)
            course_id = request.data.get('course_id')
            course = CourseOverview.objects.get(id=course_id)
            title = request.data.get('title')
            description = request.data.get('description')
            is_public = request.data.get('is_public')
            if is_public == "false" or is_public == "False":
                is_public = False
            elif is_public == "true" or is_public == "True":
                is_public = True
            image1 = request.data['image1']
           # image1 = resize_image(image1)
            
            image2 = request.data['image2']
           # image2 =resize_image(image2)
            
            image3 = request.data['image3']
            #image3 = resize_image(image3)

            image4 = request.data['image4']
            #image4 = resize_image(image4)

            image5 = request.data['image5']
            #image5 = resize_image(image5)

            image6 = request.data['image6']
            #image6 = resize_image(image6)

            data = [
                {
                    "student_id": student_id,
                    "course_id": course_id,
                    "title": title,
                    "description": description,
                    "is_public": is_public,
                }
            ]
            note_id = note.id
            if NoteImages.objects.filter(note_id=note_id).count() < 7:
                if image1 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image1,
                        created = timezone.now(),
                    )
            else:
                return Response({'error': "Note images should less than 6 photos, can't update images and delete some image.", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)

            if NoteImages.objects.filter(note_id=note_id).count() < 7:
                if image2 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image2,
                        created = timezone.now(),
                    )
            else:
                return Response({'error': "Note images should less than 6 photos, can't update images and delete some image.", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)

            if NoteImages.objects.filter(note_id=note_id).count() < 7:
                if image3 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image3,
                        created = timezone.now(),
                    )
            else:
                return Response({'error': "Note images should less than 6 photos, can't update images and delete some image.", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)

            if NoteImages.objects.filter(note_id=note_id).count() < 7:
                if image4 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image4,
                        created = timezone.now(),
                    )
            else:
                return Response({'error': "Note images should less than 6 photos, can't update images and delete some image.", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)

            if NoteImages.objects.filter(note_id=note_id).count() < 7:
                if image5 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image5,
                        created = timezone.now(),
                    )
            else:
                return Response({'error': "Note images should less than 6 photos, can't update images and delete some image.", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)

            if NoteImages.objects.filter(note_id=note_id).count() < 7:
                if image6 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image6,
                        created = timezone.now(),
                    )
            else:
                return Response({'error': "Note images should less than 6 photos, can't update images and delete some image.", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)

            setattr(note, "course_id", course)
            setattr(note, "title", title)
            setattr(note, "description", description)
            setattr(note, "is_public", is_public)
            setattr(note, "modified", timezone.now())
            note.save()
        except:
            return Response({'error': 'Not found.', 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"result": data, "status_code": status.HTTP_200_OK, "message": "Note updated successfully.", "status": True}, status=status.HTTP_200_OK) 


class FieldError(Exception):
    """Some kind of problem with a model field."""
    pass


class NoteCreateView(CreateAPIView):
    authentication_classes = (BearerAuthentication, )
    permission_classes = (IsAuthenticated, )
    parser_classes = (JSONParser, FormParser, MultiPartParser, FileUploadParser,)

    def create(self, request):
        student_id = request.user.id
        user = User.objects.get(id=student_id)
        course_id = request.data.get('course_id')
        course = CourseOverview.objects.get(id=course_id)
        try:
            enrollment = CourseEnrollment.objects.get(user=user, course=course)
        except:
            return Response({'error': 'user does not enroll course', 'status_code': status.HTTP_400_BAD_REQUEST, 'staus': False}, status=status.HTTP_400_BAD_REQUEST)
        title = request.data.get('title')
        description = request.data.get('description')
        is_public = request.data.get('is_public')
        if is_public == "false" or is_public == "False":
            is_public = False
        elif is_public == "true" or is_public == "True":
            is_public = True
            
        image1 = request.data['image1']
        image1 = resize_image(image1)
        
        image2 = request.data['image2']
        image2 =resize_image(image2)
        
        image3 = request.data['image3']
        image3 = resize_image(image3)

        image4 = request.data['image4']
        image4 = resize_image(image4)

        image5 = request.data['image5']
        image5 = resize_image(image5)

        image6 = request.data['image6']
        image6 = resize_image(image6)

        data = [
            {
                "student_id": student_id,
                "course_id": course_id,
                "title": title,
                "description": description,
                "is_public": is_public,
            }
        ]
        try:
            if not Note.objects.filter(student_id=user, course_id=course, title=title, description=description, is_public=is_public).exists():
                Note.objects.create(
                    student_id=user,
                    course_id=course,
                    title=title,
                    description=description,
                    is_public=is_public,
                    created=timezone.now(),
                    modified=timezone.now(),
                )
                try:
                    note = Note.objects.get(student_id=user, course_id=course, title=title, description=description, is_public=is_public)
                except:
                    return Response({'error': "Your Note is already exists.", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)
                if image1 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image1,
                        created = timezone.now(),
                    )

                if image2 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image2,
                        created = timezone.now(),
                    )

                if image3 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image3,
                        created = timezone.now(),
                    )
                
                if image4 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image4,
                        created = timezone.now(),
                    )
                
                if image5 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image5,
                        created = timezone.now(),
                    )

                if image6 != "":
                    NoteImages.objects.create(
                        note_id = note,
                        image = image6,
                        created = timezone.now(),
                    )
            else:
                return Response({'error': "Your Note is already exists.", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': "Not Found!!", 'status_code': status.HTTP_400_BAD_REQUEST, 'status': False}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"result": data, "status_code": status.HTTP_201_CREATED, "message": "Note created successfully.", "status": True}, status=status.HTTP_201_CREATED)




def notes(request, course_id):
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, "load", course_key)
        student_id = request.user.id
        notes = Note.objects.filter(student_id=student_id, course_id=course_id)
        user = user = User.objects.get(id=student_id)

        context = {
            "course": course,
            "notes": notes,
            "course_id": course_key,
            "user": user,
        }
        return render_to_response("note/note_home.html", context)

def peer_notes(request, course_id):
        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, "load", course_key)
        student_id = request.user.id
        notes = Note.objects.filter(is_public=True, course_id=course_id)
        user = user = User.objects.get(id=student_id)

        context = {
            "course": course,
            "notes": notes,
            "course_id": course_key,
            "user": user,
        }
        return render_to_response("note/peer_note.html", context)


def note_add(request, course_id):
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    course_overview = CourseOverview.objects.get(id=course_id)
    student_id = request.user.id
    user = user = User.objects.get(id=student_id)
    # notes = Note.objects.filter(student_id=student_id, course_id=course_id)
    context = {
        "course": course,
        "course_id": course_key,
        "user": user,
    }
    if request.method == 'POST' :
        title = request.POST['title']
        description = request.POST['description']
        is_public = request.POST.get('is_public', 0)
        if is_public == '1':
            is_public = 1
        else:
            is_public = 0
        # count = []
        count = request.POST['count']
        # str_val = ''
        # for i in count:
        #     str_val = i
        # log.error(str_val)
        arr = count.split(',')
        if arr[0] == '1':
            image1 = request.FILES['image0']
            #image1 = resize_image(image1)
            
        if arr[1] == '1':
            image2 = request.FILES['image1']
            #image2 =resize_image(image2)
            
        if arr[2] == '1':
            image3 = request.FILES['image2']
            #image3 = resize_image(image3)
            
        if arr[3] == '1':
            image4 = request.FILES['image3']
            #image4 = resize_image(image4)
            
        if arr[4] == '1':
            image5 = request.FILES['image4']
            #image5 = resize_image(image5)
            
        if arr[5] == '1':
            image6 = request.FILES['image5']
            #image6 = resize_image(image6)
            
        # log.error(image1)
        # log.error(image2)  
        # log.error(image3)
        # log.error(image4)
        # log.error(image5)  
        # log.error(image6)
        try:
            Note.objects.create(
                student_id=user,
                course_id=course_overview,
                title=title,
                description=description,
                is_public=is_public,
                created=timezone.now(),
                modified=timezone.now(),
            )
            try:
                note = Note.objects.get(student_id=user, course_id=course_overview, title=title, description=description, is_public=is_public)
                
                if arr[0] == '1':
                    if image1 != "":
                        NoteImages.objects.create(
                        note_id = note,
                        image = image1,
                        created = timezone.now(),
                        modified=timezone.now(),
                    )
                if arr[1] == '1':
                    if image2 != "":
                        NoteImages.objects.create(
                        note_id = note,
                        image = image2,
                        created = timezone.now(),
                    )
                        
                if arr[2] == '1':
                    if image3 != "":
                        NoteImages.objects.create(
                        note_id = note,
                        image = image3,
                        created = timezone.now(),
                    )
                        
                if arr[3] == '1':
                    if image4 != "":
                        NoteImages.objects.create(
                        note_id = note,
                        image = image4,
                        created = timezone.now(),
                    )
                        
                if arr[4] == '1':
                    if image5 != "":
                        NoteImages.objects.create(
                        note_id = note,
                        image = image5,
                        created = timezone.now(),
                    )
                        
                if arr[5] == '1':
                    if image6 != "":
                        NoteImages.objects.create(
                        note_id = note,
                        image = image6,
                        created = timezone.now(),
                    )
            except:
                log.error("Your Note is already exists.")     
        except Exception as ex:
            log.error(ex)
        return redirect('note_list', course_id=course_id)  
    return render_to_response("note/note_add.html", context)

def note_edit(request, course_id, pk):
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    student_id = request.user.id
    user = user = User.objects.get(id=student_id)
    note = Note.objects.get(id=pk, student_id=student_id)
    images = NoteImages.objects.filter(note_id=note)
    context = {
        "course": course,
        "note": note,
        "course_id": course_key,
        "user": user,
        "images": images,
    }
    if request.method == 'POST' :
        title = request.POST['title']
        description = request.POST['description']
        is_public = request.POST.get('is_public', 0)
        if is_public == '1':
            is_public = 1
        else:
            is_public = 0
            
        log.error(title)
        log.error(description)
        log.error(is_public)  
        count = request.POST['count']
        del_ids = request.POST['del_ids']
        log.error(del_ids)
        # del_id_list = del_ids.split(',')
        # log.error(del_id_list)
        
        # str_val = ''
        # for i in count:
        #     str_val = i
        # log.error(str_val)
        arr = count.split(',')
        log.error(arr)
            
        if arr[0] == '1':
            image1 = request.FILES['image0']
            #image1 = resize_image(image1)
            
        if arr[1] == '1':
            image2 = request.FILES['image1']
            #image2 =resize_image(image2)
            
        if arr[2] == '1':
            image3 = request.FILES['image2']
            #image3 = resize_image(image3)
            
        if arr[3] == '1':
            image4 = request.FILES['image3']
            #image4 = resize_image(image4)
            
        if arr[4] == '1':
            image5 = request.FILES['image4']
            #image5 = resize_image(image5)
            
        if arr[5] == '1':
            image6 = request.FILES['image5']
            #image6 = resize_image(image6)
        try:
            del_id_arr = [int(x) for x in del_ids.split(',')]
            del_id_arr.pop(0)
            if len(del_id_arr) > 0:
                NoteImages.objects.filter(id__in=del_id_arr).delete()
                
            setattr(note, "title", title)
            setattr(note, "description", description)
            setattr(note, "is_public", is_public)
            setattr(note, "modified", timezone.now())
            note.save()
            
            if arr[0] == '1':
                if image1 != "":
                    NoteImages.objects.create(
                    note_id = note,
                    image = image1,
                    created = timezone.now(),
                    modified=timezone.now(),
                )
            if arr[1] == '1':
                if image2 != "":
                    NoteImages.objects.create(
                    note_id = note,
                    image = image2,
                    created = timezone.now(),
                )
                    
            if arr[2] == '1':
                if image3 != "":
                    NoteImages.objects.create(
                    note_id = note,
                    image = image3,
                    created = timezone.now(),
                )
                    
            if arr[3] == '1':
                if image4 != "":
                    NoteImages.objects.create(
                    note_id = note,
                    image = image4,
                    created = timezone.now(),
                )
                    
            if arr[4] == '1':
                if image5 != "":
                    NoteImages.objects.create(
                    note_id = note,
                    image = image5,
                    created = timezone.now(),
                )
                    
            if arr[5] == '1':
                if image6 != "":
                    NoteImages.objects.create(
                    note_id = note,
                    image = image6,
                    created = timezone.now(),
                )
                    
            
        except Exception as ex:
            log.error(ex)
        return redirect('note_list', course_id=course_id)  
    return render_to_response("note/note_edit.html", context)


def peer_detail(request, course_id, pk):
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    student_id = request.user.id
    user = user = User.objects.get(id=student_id)
    note = Note.objects.get(id=pk)
    images = NoteImages.objects.filter(note_id=note)
    context = {
        "course": course,
        "note": note,
        "course_id": course_key,
        "user": user,
        "images": images,
    } 
    if request.method == 'POST' :
        return redirect('peer_notes', course_id=course_id)  
    return render_to_response("note/peer_detail.html", context)
