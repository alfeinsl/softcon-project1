from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib import messages
from django.db.models import Q

from opah_mc.models import Plant, PlantBenefits, PlantTips, Comment, Comment_Like_Dislike
from opah_mc.forms.opah_mc import CommentForm, PlantForm, PlantBenefitsForm, PlantTipsForm, ReportForm
from opah_mc.models.opah_mc.report import Report


def all_plants(request):
  plants = Plant.objects.all()
  context = {
      "plants": plants,
  }
  return render(request, "home/plant/plant_all.html", context)


@permission_required('opah_mc.add_plant', all_plants)
def add_plant(request):
  if request.method == "POST":
    if request.POST.get("gplant_id") == "":
      # Change gplant post value
      post = request.POST.copy()
      post['gplant_id'] = None
      request.POST = post
    
    plant_form = PlantForm(request.POST)
    
    if plant_form.is_valid():
      plant_form.save()
      messages.success(request, "New Plant Added." )
      return redirect("all_plants")
    
    messages.error(request, "Failed to add new plant. " + plant_form.errors)
    print(plant_form.errors) 
    
  # Else if not POST
  plant_form = PlantForm()
  gplants = Plant.objects.filter(gplant_id=None)
  return render (request = request,
                 template_name = "home/plant/plant_add.html",
                 context = {"plant_form": plant_form,
                            "gplants": gplants})
  

def a_plant(request, plant_id):
  plant = Plant.objects.get(id=plant_id)
  
  gplant = None
  sub_plants = None
  if plant.gplant_id is not None:
    gplant = Plant.objects.get(id=plant.gplant_id)
  else:
    sub_plants = Plant.objects.filter(gplant_id = plant.id)
    
  benefits = PlantBenefits.objects.filter(plant=plant)
  tips = PlantTips.objects.filter(plant=plant)
    
  report_form = ReportForm()
  
  comment_form = CommentForm()
  comments = Comment.objects.filter(plant=plant)
  
  context = {
    "plant": plant,
    "gplant": gplant,
    "sub_plants": sub_plants,
    "benefits": benefits,
    "tips": tips,
    
    "report_form": report_form,
    
    "comment_form": comment_form,
    "comments": comments,
  }
  
  if request.user.is_authenticated and request.user.member.is_manager() == True:
    contextManager = prepare_plant_manager(plant)
    context.update(contextManager)
  
  return render(request, "home/plant/plant.html", context)


def prepare_plant_manager(plantR):
  benefit_form = PlantBenefitsForm()
  tip_form = PlantTipsForm()
  
  reportsAll = Report.objects.filter(plant=plantR)
  
  reportsPending   = Report.objects.filter(status=0, plant=plantR)
  reportsReviewed  = Report.objects.filter(status=1, plant=plantR)
  reportsApproved  = Report.objects.filter(status=2, plant=plantR)
  reportsDenied    = Report.objects.filter(status=3, plant=plantR)
  
  reportsStatus = [
    ("Pending"  , reportsPending),
    ("Reviewed" , reportsReviewed),
    ("Approved" , reportsApproved),
    ("Denied"   , reportsDenied),
  ]
  
  context = {
    "benefit_form": benefit_form,
    "tip_form": tip_form,
    
    "reportsAll": reportsAll,
    "reportsStatus": reportsStatus,
  }
  
  return context


@permission_required('opah_mc.change_plant', all_plants)
def edit_plant(request, plant_id):
  plant = Plant.objects.get(id=plant_id)
  
  if request.method == "POST":
    plant_form = PlantForm(request.POST, instance=plant)
    if plant_form.is_valid():
      plant.update_model_date()
      plant.save()
      plant = plant_form.save()
      messages.success(request, "Save Plant SuCcessfully." )
      return redirect("plant", plant_id=plant.id)
    messages.error(request, "Failed to edit Plant Information. " + plant_form.errors)
    
  gplants = Plant.objects.filter(Q(gplant_id=None), ~Q(id=plant.id))
  context = {
    "plant": plant,
    "gplants": gplants,
  }
  return render(request, "home/plant/plant_edit.html", context)


@permission_required('opah_mc.delete_plant', all_plants)
def delete_plant(request, plant_id):
  plant = Plant.objects.get(id=plant_id)
  plant.delete()
  return redirect("all_plants")


@login_required
def report_plant(request):
  if request.method == "POST":
    report_form = ReportForm(request.POST)
    plant_id = request.POST.get('plant')
    if plant_id == "None":
      report_form.fields.pop("plant")
    
    if report_form.is_valid():
      report = report_form.save()
      messages.success(request, "New Report Submitted." )
      return redirect("report", report_id=report.id)
    
    messages.error(request, "Failed to add Report. " + report_form.errors)
    print(report_form.errors)
  return redirect("home")


@permission_required('opah_mc.add_plantbenefits', all_plants)
def add_plant_benefit(request):
  if request.method == "POST":
    benefit_form = PlantBenefitsForm(request.POST)
    plant_id = request.POST.get('plant')
    
    if benefit_form.is_valid():
      benefit_form.save()
      messages.success(request, "New Benefit added." )
    else:
      messages.error(request, benefit_form.errors)
      print(benefit_form.errors)
    
    return redirect("plant", plant_id=plant_id)
  return redirect("all_plants")


@permission_required('opah_mc.add_planttips', all_plants)
def add_plant_tip(request):
  if request.method == "POST":
    tip_form = PlantTipsForm(request.POST)
    plant_id = request.POST.get('plant')
    
    if tip_form.is_valid():
      tip_form.save()
      messages.success(request, "New Tip added." )
    else:
      messages.error(request, tip_form.errors)
      print(tip_form.errors)
    
    return redirect("plant", plant_id=plant_id)
  return redirect("all_plants")


def add_plant_comment(request):
  if request.method == "POST":
    comment_form = CommentForm(request.POST)
    plant_id = request.POST.get('plant')
    
    if comment_form.is_valid():
      comment_form.save()
      messages.success(request, "New Comment added." )
    else:
      messages.error(request, "Failed to add Comment. " + comment_form.errors)
  return redirect("plant", plant_id=plant_id)


def update_comment_like_dislike(request):
  if request.method == "POST":
    comment_id  = request.POST.get('comment_id')
    comment     = Comment.objects.get(id=comment_id)
    status      = request.POST.get('status')
    
    comment_like_dislike, created = Comment_Like_Dislike.objects.update_or_create(
      user      = request.user,
      comment   = comment
    )
    if comment_like_dislike.is_liked == True and status == "1" or comment_like_dislike.is_liked == False and status == "2":
      print("revert to none")
      comment_like_dislike.is_liked = None
    elif status == "1":
      print("like comment")
      comment_like_dislike.is_liked = True
    elif status == "2":
      print("dislike comment")
      comment_like_dislike.is_liked = False
    else:
      print(status)
    
    print(comment_like_dislike.is_liked)
    print(comment_like_dislike)
    print(created)
    comment_like_dislike.save()
    context={
      "like_count": comment.get_total_like(),
      "dislike_count": comment.get_total_dislike()
    }
    
    return JsonResponse(context)