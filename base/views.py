from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm
from datetime import date
from django.http import HttpResponse

# Create your views here.
# rooms = [
#     {'id': 1, 'name': 'a website!!1'},
#     {'id': 2, 'name': 'a website!!2'},
#     {'id': 3, 'name': 'a website!!3'},
# ]


def loginRedirect(request):
    messages.error(request, 'This email already has already been registered.')
    return redirect('login')


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist.')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            if ((date.today() - user.last_room_date).days >= 7):
                user.rooms_this_week = 0
                user.save()

            messages.success(
                request, f'Successfully signed in as {user.username}.')
            return redirect('home')
        else:
            messages.error(request, 'Username or password does not exist')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'base/login_register.html', {'form': form})


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(Q(topic__name__icontains=q) |
                                Q(name__icontains=q) |
                                Q(description__icontains=q))

    topics = Topic.objects.all()[:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms': rooms,
               'topics': topics,
               'room_count': room_count,
               'room_messages': room_messages, }

    return render(request, 'base/home.html', context)


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'user': user,
               'rooms': rooms,
               'room_messages': room_messages,
               'topics': topics,
               }
    return render(request, 'base/profile.html', context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')

    participants = room.participants.all()
    waiting_room = room.waiting_room.all()

    if request.method == 'POST':
        contains_link = False
        contains_img = False
        contains_video = False
        img = ''
        video = ''
        msg = request.POST.get('body')

        if request.POST.get('invite'):
            if request.user not in room.waiting_room.all():
                room.waiting_room.add(request.user)
                messages.success(request, 'Request sent.')
            else:
                messages.success(request, 'You already sent a request.')

        if request.user == room.host:
            review = request.POST.get('review')
            if review and review.startswith('accept'):
                user_id = int(review.split(' ')[1])
                user = User.objects.get(id=user_id)
                room.participants.add(user)
                room.waiting_room.remove(user)
            elif review and review.startswith('deny'):
                user_id = int(review.split(' ')[1])
                user = User.objects.get(id=user_id)
                room.waiting_room.remove(user)

        if not msg:
            return redirect('room', pk=room.id)

        msg_split = msg.split()
        for word in msg_split:
            if word.startswith('http') or word.startswith('www.'):
                contains_link = True
            if word[-4:] in ['.jpg', 'webp', '.png', 'jpeg', '.ico', '.svg']:
                contains_img = True
                img = word
            if 'www.youtube.com' in word:
                contains_video = True
                video = word[word.index('=')+1:]

        message = Message.objects.create(
            user=request.user,
            room=room,
            body=msg,
            img=img,
            video=video,
            contains_link=contains_link,
            contains_img=contains_img,
            contains_video=contains_video,
        )

        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {
        'Room': room,
        'room_messages': room_messages,
        'participants': participants,
        'waiting_room': waiting_room,
    }
    return render(request, 'base/room.html', context)


@login_required(login_url='/login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        try:
            if Room.objects.get(name=name):
                messages.error(request, 'That name is already in use')
                return redirect('create-room')
        except:
            pass
        if request.user.rooms_this_week < 3:
            request.user.rooms_this_week += 1
            request.user.save()

            topic_name = request.POST.get('topic')
            topic, created = Topic.objects.get_or_create(name=topic_name)
            private = False
            if request.POST.get('private'):
                private = True

            Room.objects.create(
                host=request.user,
                topic=topic,
                name=name,
                description=request.POST.get('description'),
                private=private,
                banner=request.POST.get('banner'),
            )

            room = Room.objects.get(
                name=request.POST.get('name'), host=request.user)
            room.participants.add(request.user)

        else:
            messages.error(
                request, 'You can\'t create more than 3 spaces per week!')
        # form = RoomForm(request.POST)
        # if form.is_valid():
        #     room = form.save(commit=False)
        #     room.host = request.user
        #     room.save()
        return redirect('home')

    context = {
        'form': form,
        'topics': topics,
    }

    return render(request, 'base/room_form.html', context)


@login_required(login_url='/login')
def update_room(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        messages.error(request, 'You can\'t edit someone else\'s space!')
        return redirect('home')

    if request.method == 'POST':
        # form = RoomForm()
        # topics = Topic.objects.all()
        # form = RoomForm(request.POST, instance=room)
        name = request.POST.get('name')
        try:
            if Room.objects.get(name=name):
                messages.error(request, 'That name is already in use')
                return redirect('update-room', pk=pk)
        except:
            pass
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = name
        if room.topic != topic and room.topic.room_set.all().count() == 1:
            room.topic.delete()
        room.topic = topic
        room.description = request.POST.get('description')
        room.banner = request.POST.get('banner')
        if request.POST.get('private'):
            room.private = True
        else:
            room.private = False
        room.save()
        # if form.is_valid():
        #     form.save()
        return redirect('home')

    context = {'form': form,
               'topics': topics,
               'room': room,
               }
    return render(request, 'base/room_form.html', context)


@login_required(login_url='/login')
def delete_room(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        messages.error(request, 'You can\'t delete someone else\'s space!')
        return redirect('home')

    if request.method == 'POST':
        if room.topic.room_set.all().count() == 1:
            room.topic.delete()
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='/login')
def delete_message(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        messages.error(request, 'You can\'t delete someone else\'s message!')
        return redirect('home')

    if request.method == 'POST':
        room = message.room
        message.delete()
        return redirect(f'/room/{room.id}')

    return render(request, 'base/delete.html', {'obj': message})


@login_required(login_url='login')
def update_user(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    context = {
        'form': form,
    }

    return render(request, 'base/update-user.html', context)


def topics_page(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)

    context = {
        'topics': topics,
    }

    return render(request, 'base/topics.html', context)


def activity_page(request):
    room_messages = Message.objects.all()

    context = {
        'room_messages': room_messages,
    }

    return render(request, 'base/activity.html', context)


def report(request, pk):

    user = User.objects.get(id=pk)

    if request.method == 'POST':
        reason = request.POST.get('report')
        if reason == 'messages':
            user.report_messages += 1
            user.save()
            if user.report_messages >= 10:
                delete_rooms(user)
                user.delete()
            return redirect('home')
        elif reason == 'username':
            user.report_username += 1
            user.save()
            if user.report_username >= 10:
                delete_rooms(user)
                user.delete()
            return redirect('home')
        elif reason == 'picture':
            user.report_picture += 1
            user.save()
            if user.report_picture >= 10:
                delete_rooms(user)
                user.delete()
            return redirect('home')

    context = {
        'user': user,
    }

    return render(request, 'base/report.html', context)


def delete_rooms(user):
    rooms = user.room_set.all()
    for room in rooms:
        if room.topic.room_set.all().count() == 1:
            room.topic.delete()
        room.delete()


def handle_not_found(request, exception):
    return render(request, 'error.html')


def handle_server_error(request):
    return render(request, 'error.html')
