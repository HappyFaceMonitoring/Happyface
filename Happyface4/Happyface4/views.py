from django.apps import apps
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.views.defaults import page_not_found

from . import utilities as ut


def home(request):
    # get the time from the request, otherwise use the current time
    link_date, request_time, form, reload = ut.extract_time_from_request(request)

    # get the list of relevant apps that are to be displayed in the categories bar
    analyses = ut.get_Analyses_from_apps(apps)

    # get the instance and category statuses from the different analyses instances and
    # the overall worst status from request_time 24 h into the past
    # used for the status display in the nav bar as well as for the status Overview module
    statuses = ut.get_statuses_of_instances(
        analyses, request_time, time_range=settings.OVERVIEW_RANGE
    )

    context = {
        "statuses": statuses,
        "form": form,
        "time": request_time,
        "link_date": link_date,
        "reload": reload,
        "commit_sha": settings.COMMIT_SHA,
        "legals_url": settings.LEGALS_URL,
        "documentation_url": settings.DOCUMENTATION_URL,
    }

    return render(request, "home.html", context=context)


def index(request, category):
    # get the time from the request, otherwise use the current time
    link_date, request_time, form, reload = ut.extract_time_from_request(request)

    # get the list of relevant apps that are to be displayed in the categories bar
    analyses = ut.get_Analyses_from_apps(apps)

    # create the objects that will be displayed in the category part of the site
    statuses = ut.get_statuses_of_instances(
        analyses, request_time, time_range=settings.PULL_INTERVAL
    )

    # render the instances in the category requested
    divs = ut.render_instances(analyses, category, request_time, request)

    # catch case where the category string doesn't match the category of any analysis
    if not divs:
        return page_not_found(request, "This category is not available.")

    # generate the context for the rendering of the template
    context = {
        "divs": divs,
        "statuses": statuses,
        "form": form,
        "time": request_time,
        "link_date": link_date,
        "reload": reload,
        "commit_sha": settings.COMMIT_SHA,
        "legals_url": settings.LEGALS_URL,
        "documentation_url": settings.DOCUMENTATION_URL,
    }

    # get the template
    template = loader.get_template("index.html")

    # return the rendered Template as a HTTP response
    return HttpResponse(template.render(context, request))
