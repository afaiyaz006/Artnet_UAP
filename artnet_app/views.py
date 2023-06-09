
from django.shortcuts import render,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,authenticate
from .artengine import process_image,image_to_byte,create_generated_artwork
from artnet_app.forms import Imageform,ArtWork_with_selected_artstyle_form, SignupForm,ArtStyleForm,TextPromptForm
from .models import ArtComment, ArtWork,ArtStyle,SimpleImageUpload,Profile,GeneratedArtwork
from django.core.files.base import ContentFile
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.urls import reverse
from django.shortcuts import render,redirect
from .forms import SignupForm,ArtWork_with_Famous_ArtStyle
from django.core.paginator import Paginator
from .models import Notifications

# Creating my  views here.

def home(request):
    """
    The home of the
    webpage.
    
    """
    #loading all  artworks 
    
    artworks=ArtWork.objects.order_by("post_date")
    paginator=Paginator(artworks,2) # show 2 artworks per page
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    if request.user.is_authenticated:
        notifications=Notifications.objects.filter(notify_user=request.user,is_read=False).order_by("-timestamp")
    else:
        notifications=[]
    if len(notifications)==0:
        notifications=None
    return render(request,'artnet_app/home.html',{'artworks':artworks,'page_obj':page_obj,'ns':notifications})

@login_required
def profileview(request):
    '''
    Show User profile
    '''
    artworks=ArtWork.objects.filter(author=request.user.id)
    artstyles=ArtStyle.objects.filter(art_author=request.user.id)
    
    return render(request,'artnet_app/profile.html',{'artworks':artworks,'artstyles':artstyles})

@login_required
def create_artwork_view(request):
    """Process images uploaded by users"""
    print(request.user)
    
    if request.method == 'POST':
       
        form = Imageform(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # Get the current artwork instance object to display in the template
            form_obj=form.instance
            artwork_name=form.cleaned_data['artwork_name']
            
            ordinary_image_url=form_obj.ordinary_image.path
            artwork_image_url=form_obj.artwork_image.path

            artstyle_image=form_obj.artwork_image
            
            created_artwork=process_image(ordinary_image_url,artwork_image_url)#api call need to be carefull
            user_instance = request.user
            #if 'http://' not in get_artwork_url:
            #    return render(request, 'artnet_app/artwork_creation_unsuccessfull.html')
            artwork = ArtWork()
            artstyle = ArtStyle()
            artwork.name = artwork_name
            artwork.author = user_instance
    
            if created_artwork:
                # first we are saving the style
                artstyle.art_author=user_instance
                artstyle.style_name=artwork.name+" style "
                artstyle.artStyle_image=artstyle_image
                artstyle.save()
                
                #associating artstyle with artworks
                artwork.artstyle_used=artstyle

                #saving the artwork
                artwork_file_name=str(artwork_name+".jpg")
                artwork.artwork_image.save(artwork_file_name,ContentFile(image_to_byte(created_artwork),name=artwork_file_name),save=True)
                
                return render(request, 'artnet_app/artwork_creation_successful.html', {'artwork':artwork})
            else:
                return render(request, 'artnet_app/artwork_creation_unsuccessful.html')
             
    else:
        form=Imageform()
        
    return render(request, 'artnet_app/artwork_create.html', {'form': form})

@login_required
def create_artwork_with_selected_style_view(request):
    """
        Processing image uploaded by user
    """
    if request.method=='POST':
        form=ArtWork_with_selected_artstyle_form(request.POST,request.FILES)
        if  form.is_valid():
            form.save()
            form_obj=form.instance
            artwork_name=form.cleaned_data['artwork_name']
            artstyle=request.session.get('artstyle_id',None)
            associated_artstyle=ArtStyle.objects.filter(pk=artstyle)[0]
            
            if not associated_artstyle:
                return render(request, 'artnet_app/artwork_creation_unsuccessful.html')

            ordinary_image_url=form_obj.ordinary_image.path
            artstyle_image_url=associated_artstyle.artStyle_image.path
            

            created_artwork=process_image(ordinary_image_url,artstyle_image_url)#api call
            user_instance=request.user

            artwork=ArtWork()
            

            artwork.name=artwork_name
            artwork.author=user_instance
            
            print(ordinary_image_url)
            print(artstyle_image_url)

          
            if created_artwork:
                #artstyle is already saved so just making it the foreign key of the new artwork
                artwork.artstyle_used=associated_artstyle

                #saving the artwork
                artwork_file_name=str(artwork_name+".jpg")
                artwork.artwork_image.save(artwork_file_name,ContentFile(image_to_byte(created_artwork),name=artwork_file_name),save=True)
                
                return render(request, 'artnet_app/artwork_creation_successful.html', {'artwork':artwork})
            else:
                return render(request, 'artnet_app/artwork_creation_unsuccessful.html')

    else:
        artstyle=request.session.get('artstyle_id',None)
        associated_artstyle=ArtStyle.objects.filter(pk=artstyle)[0]
        artstyle_name=associated_artstyle.style_name
        form=ArtWork_with_selected_artstyle_form()
        
    return render(request,'artnet_app/artwork_create_with_selected_artstyle.html',{'form':form,'choosen_style':artstyle_name})

@login_required
def famousArtWorkCreation(request):
    if request.method=='POST':
        form=ArtWork_with_Famous_ArtStyle(request.POST,request.FILES)
        if form.is_valid():
            artwork_name=form.cleaned_data['artwork_name']
            artstyle=form.cleaned_data['famous_artstyle']
            ordinary_image=request.FILES['ordinary_image']
            #print(f"{artstyle}-------> {type(artstyle)}")
            #print(f"{ordinary_image}------->{type(ordinary_image)}")

            image_storage=SimpleImageUpload()
            image_storage.normal_image=ordinary_image
            image_storage.save()
           
            ordinary_image_url=image_storage.normal_image.path
            artstyle_image_url=artstyle.artStyle_image.path
            #print(ordinary_image_url)
            #print(artstyle_image_url)
            created_artwork=process_image(ordinary_image_url,artstyle_image_url)#api call
            
            artwork=ArtWork()
            if created_artwork:
                artwork.name=artwork_name
                artwork.author=request.user
                artwork.artstyle_used=artstyle
                artwork_file_name=str(artwork_name+".jpg")
                artwork.artwork_image.save(artwork_file_name,ContentFile(image_to_byte(created_artwork),name=artwork_file_name),save=True)
                
                return render(request, 'artnet_app/artwork_creation_successful.html', {'artwork':artwork})
            else:
                return render(request, 'artnet_app/artwork_creation_unsuccessful.html')
    
    else:
        form=ArtWork_with_Famous_ArtStyle()    
    return render(request,'artnet_app/artwork_create_with_famous_artstyle.html',{'form':form})


@login_required
def artStyleSubmitView(request):
    if request.method=='POST':
        form=ArtStyleForm(request.POST,request.FILES)
        if form.is_valid():
            print('success')
            form.save()
            artstyle=ArtStyle()
            artstyle.art_author=request.user
            artstyle.style_name=form.cleaned_data['style_name']
            artstyle.artStyle_image=form.cleaned_data['artStyle_image']
            artstyle.save()
            return render(request,'artnet_app/artstyle_submission_successful.html',{'artstyle':artstyle})
            
    else:
        print("empty")
        form=ArtStyleForm()
    return render(request,'artnet_app/artstyle_submit.html',{'form':form})

class ProfileDetailView(generic.DetailView):
    """
        Generic class based view for detail view of user profile
    """
    model=Profile
    template_name='artnet_app/profile_detail.html'
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        displayed_user=self.get_object()
        artworks=ArtWork.objects.filter(author=displayed_user.user.id)
        artstyles=ArtStyle.objects.filter(art_author=displayed_user.user.id)
        context['artstyles']=artstyles
        context['artworks']=artworks
        return context

class ProfileListView(generic.ListView):
    """
        Generic class based view for list view of user profiles
    """
    model=Profile
    template_name='artnet_app/profile_list.html'
    
class ArtWorkListView(generic.ListView):
    """
    Generic class based view for a list of artworks
    """
    model=ArtWork
    paginate_by = 6

class ArtWorkDetailView(generic.DetailView):
    """
    Generic class-based detail view for a artwork
    """
    model=ArtWork
    
    def get_context_data(self, **kwargs):
        """
           Overriding this method To include associated artstyle of 
           the artwork to be  displayed.
        """
        context=super().get_context_data(**kwargs)
        displayed_artwork=self.get_object()
        associated_artwork=displayed_artwork.artstyle_used
        self.request.session['artstyle_id']=associated_artwork.id
        #storing the artstyle_id so that it could be used in artwork_create view
        context['artstyle_id']=self.request.session['artstyle_id']
        #passing the artstyle variable to template
        context['artstyle']=associated_artwork 
            
            
        return context

class ArtStyleDetailView(generic.DetailView):
    model=ArtStyle
    def get_context_data(self,**kwargs):
        context=super().get_context_data(**kwargs)
        displayed_artstyle=self.get_object()
        self.request.session['artstyle_id']=displayed_artstyle.id
        context['artstyle_id']=displayed_artstyle.id
        context['artstyle']=displayed_artstyle
        return context


class ArtWorkCommentCreate(LoginRequiredMixin,generic.CreateView):
    """
    Artwork comment creation code.
    """
    model=ArtComment
    fields=['description']
    def get_context_data(self, **kwargs):
        """
        Add associated Artwork to form template so can display its title in HTML.
        """
        # Call the base implementation first to get a context
        context = super(ArtWorkCommentCreate, self).get_context_data(**kwargs)
        # Get the artwork from id and add it to the context
        context['artwork'] = get_object_or_404(ArtWork, pk = self.kwargs['pk'])
        return context
        
    def form_valid(self, form):
        """
        Add author and associated artwork to form data before setting it as valid (so it is saved to model)
        """
        #Add logged-in user as author of comment
        form.instance.author = self.request.user
        #Associate comment with artwork based on passed id
        form.instance.artwork=get_object_or_404(ArtWork, pk = self.kwargs['pk'])

        #notification behavior
        
        from_user=self.request.user.username
        to_user=form.instance.artwork.author
        if from_user!=to_user.username:
            artwork_url=form.instance.artwork.get_absolute_url()
            notifcation_message=f"{from_user} commented on your artwork <a href='{artwork_url}'>See Details</a>"

            #print(notifcation_message)
            n=Notifications.objects.create(is_read=False,notify_user=to_user,message=notifcation_message)
            n.save()


        # Call super-class form validation behaviour
        return super(ArtWorkCommentCreate, self).form_valid(form)

    def get_success_url(self): 
        """
        After posting comment return to associated artwork.
        """
        return reverse('artwork-detail', kwargs={'pk': self.kwargs['pk'],})


def signup(request):
    if request.method=='POST':
        form=SignupForm(request.POST)
        if form.is_valid():
            user=form.save()
            user.refresh_from_db()
            user.profile.gender=form.cleaned_data.get('gender')
            user.profile.occupation=form.cleaned_data.get('occupation')
            avatar_url="https://avatars.dicebear.com/api/adventurer-neutral/"+str(user.username)+'.svg'+'?r=50'
            user.profile.avatar_link=avatar_url
            user.save()
            raw_password=form.cleaned_data.get('password1')
            user = authenticate(username=user.username,password=raw_password)
            login(request,user)
            return redirect('home')
    else:
        
        form=SignupForm()
        
    return render(request,'registration/signup.html',{'form':form})

@login_required
def like_artwork(request,id):
    
    if request.method == "POST":
        artwork = ArtWork.objects.get(id=id)
        if not artwork.likes.filter(id=request.user.id).exists():
            print(f"User ID: {request.user.id} Liked artwork Artwork ID: {artwork.id}.")
            if request.user.id!=artwork.author.id:
                from_user = User.objects.get(id=request.user.id)
                to_user=artwork.author
                notification_message=f"{from_user.username} liked your artwork <a href='{artwork.get_absolute_url()}'>{artwork.name}</a>"
                print(notification_message)
                n=Notifications.objects.create(is_read=False,notify_user=to_user,message=notification_message)
                n.save()
            artwork.likes.add(request.user)
            artwork.save()

            return render( request, 'artnet_app/partials/like_area.html', context={'artwork':artwork})
        
        else:
            print(f"User ID: {request.user.id} unliked Artwork ID: {artwork.id}.")
            artwork.likes.remove(request.user)
            artwork.save() 
            return render( request, 'artnet_app/partials/like_area.html', context={'artwork':artwork})    



def searchview(request):
    if request.GET:
        q=request.GET['sq']
        artworks=ArtWork.objects.filter(name__icontains=q)
        users=User.objects.filter(username__icontains=q)
        artstyles=ArtStyle.objects.filter(style_name__icontains=q)
        return render(request,'artnet_app/search.html',{'users':users,'artworks':artworks,'artstyles':artstyles})
    
    return render(request,'artnet_app/search.html',{'users':None,'artworks':None})

@login_required
def generatedArtworkCreation(request):
    if request.method=='POST':
        form=TextPromptForm(request.POST)
        if form.is_valid():
            prompt=form.cleaned_data['prompt']
            artwork=create_generated_artwork(prompt)
            if artwork==None:
                return render(request,'artnet_app/generated_artwork_create.html',{'form':form,'errors':"Server is down or having difficulties processing.Please try again or whatever."})
            print(f"What: {artwork}")
            generatedArtWork=GeneratedArtwork()
            generatedArtWork.author=request.user
            artwork_file_name=str(prompt+".jpg")
            generatedArtWork.artwork_image.save(artwork_file_name,ContentFile(image_to_byte(artwork),name=artwork_file_name),save=True)
            return render(request, 'artnet_app/artwork_creation_successful.html', {'artwork':generatedArtWork})
            
    else:
        print("empty")
        form=TextPromptForm()
    return render(request,'artnet_app/generated_artwork_create.html',{'form':form})

@login_required
def clear_notifications(request,id):
    #print(f"{id}")
    if request.method=='GET':
        to_user=User.objects.get(id=id)
        notifications=Notifications.objects.filter(notify_user=to_user)
        print(notifications)
        for notification in notifications:
            notification.is_read=True
            notification.save()
        return home(request)
    else:
        return home(request)

@login_required
def get_likes(request,id):
    if request.method=='GET':
        artwork = ArtWork.objects.get(id=id)
        if artwork:
            return render(request,'artnet_app/partials/likes.html',{'artwork':artwork})

@login_required
def get_notifications(request):
    if request.method=='GET':
        ns=Notifications.objects.filter(notify_user=request.user,is_read=False).order_by("-timestamp")
        if ns:
            return render(request,'artnet_app/partials/notification_area.html',{'ns':ns})  
        else:
            return render(request,'artnet_app/partials/notification_area.html',{'ns':None})

@login_required
def notificationview(request):
    nts=Notifications.objects.filter(notify_user=request.user).order_by("-timestamp")
    
    return render(request,'artnet_app/notifications.html',{'nts':nts})

@login_required
def emotionRecognition(request):
    return render(request,'artnet_app/emotion_recognition.html')
