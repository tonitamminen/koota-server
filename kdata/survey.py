import base64
from calendar import timegm
import datetime
import json
from json import loads, dumps
import os
import six

#from django import forms
from django.conf import settings
from django.contrib.admin import widgets as admin_widgets
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, Http404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse

import floppyforms as forms

from . import converter
from . import models
from . import devices
from . import util
from . import views


class _SurveyField(object):
    widget = None
    def __init__(self, question):
        self.question = question
class Bool(_SurveyField):
    field = forms.BooleanField
class Char(_SurveyField):
    field = forms.CharField
class Choice(_SurveyField):
    def __init__(self, question, choices):
        self.question = question
        self.choices = choices
class Integer(_SurveyField):
    field = forms.IntegerField
class Time(_SurveyField):
    field = forms.TimeField
    widget = forms.TimeInput
#    widget = admin_widgets.AdminTimeWidget

def field_to_json(x):
    if isinstance(x, _SurveyField):
        return (x.__class__.__name__,
                x.__dict__)
    if isinstance(x, datetime.time):
        return x.strftime('%H:%M:%S')
    if isinstance(x, datetime.datetime):
        return timegm(x.utctimetuple())
    if isinstance(x, datetime.date):
        return x.strftime('%Y-%m-%d')
    raise ValueError("JSON enocde error: unknown type: %r"%x)
json_encode = json.JSONEncoder(default=field_to_json).encode


def make_form(data):
    """Take Python data and return a django.forms.Form."""
    form_fields = { }
    for i, (tag, row) in enumerate(data):
        if isinstance(row, Choice):
            form_fields[tag] = forms.ChoiceField(
                [(i,x) for i,x in enumerate(row.choices)],
                label=row.question,
                widget=forms.RadioSelect,
                required=False)
        else:
            form_fields[tag] = row.field(label=row.question, required=False,
                                         widget=row.widget)

    Form = type('DynamicSurveyForm',
                (forms.Form, ),
                form_fields)
    return Form


def take_survey(request, token):
    """This is the view which handles surveys."""
    context = c = { }
    # Find the survey data via token, then find the
    try:
        token_row = models.SurveyToken.objects.get(token=token)
    except models.SurveyToken.DoesNotExist:
        return HttpResponse('Survey %s does not exist...'%token,
                            status=404)
    device = models.SurveyDevice.get_by_id(token_row.device_id)
    survey_class = device.get_class()

    survey_data = survey_class.get_survey(data=token_row.data, device=device)

    Form = make_form(survey_data['questions'])
    survey_name = c['survey_name'] = survey_data.get('name', survey_class.__name__)

    if request.method == 'POST':
        form = c['form'] = Form(request.POST)
        if form.is_valid():
            token_row.ts_submit = timezone.now()
            # make the json
            #import IPython ; IPython.embed()
            data = { }
            data['survey_data'] = dict(survey_data)
            data['survey_name'] = survey_data.get('name', survey_class.__name__)
            data['token'] = token
            data['answers'] = { }
            # Go through and record all answers.
            for tag, field in form.fields.items():
                q = field.label
                a = form.cleaned_data[tag]
                data['answers'][tag] = dict(q=q, a=a)

            # Save the data
            data['access_time'] = token_row.ts_access
            data['submit_time'] = token_row.ts_submit
            data = json_encode(data)
            views.save_data(data=data, device_id=token_row.device_id,
                            request=request)
            #print(data)
            c['success'] = True
        else:
            pass
    else:
        token_row.ts_access = timezone.now()
        form = c['form'] = Form()
    token_row.save()
    return TemplateResponse(request, 'koota/survey.html', context)





class SurveyAnswers(converter._Converter):
    header = ['id', 'question', 'answer']
    desc = "Survey questions and answers"
    def convert(self, rows, time=lambda x:x):
        for ts, data in rows:
            data = loads(data)
            for slug, x in data['answers'].items():
                yield slug, x['q'], x['a'];
class SurveyMeta(converter._Converter):
    header = ['name', 'access_time', 'submit_time', 'seconds', 'n_questions']
    desc = "Survey questions and answers"
    def convert(self, rows, time=lambda x:x):
        for ts, data in rows:
            data = loads(data)
            yield (data.get('survey_name', None),
                   data['access_time'],
                   data['submit_time'],
                   data['submit_time']-data['access_time'],
                   len(data['answers']),
                   )




class _SurveyMetaclass(type):
    """Automatically register new devices

    This metaclass will call devices.register_device automatically
    upon class creation.
    """
    def __new__(mcs, name, bases, dict):
        cls = type.__new__(mcs, name, bases, dict)
        if (cls.__name__ != 'BaseSurvey'
            and not cls.__name__.startswith('_')
            and dict.get('_register_device', True)
           ):
            devices.register_device(cls)
        return cls

from . import converter
@six.add_metaclass(_SurveyMetaclass)
class BaseSurvey(devices._Device):
    dbmodel = models.SurveyDevice
    converters = [converter.Raw,
                  SurveyAnswers,
                  SurveyMeta,
                 ]

    @classmethod
    def get_survey(cls, data, device):
        """This method should be overwritten to return the survey data."""
        raise NotImplementedError("This survey is not yet configured, "
                                  "define get_survey().")

    @classmethod
    def create_hook(cls, instance, user):
        """In this create hook, do survey specifc setup.

        Mainly, this is used for making the survey tokens and for
        ephemeral surveys, any setup needed there.
        """
        super(BaseSurvey, cls).create_hook(instance, user)
        device_id = instance.device_id

        # Set any tokens we need
        token = base64.b16encode(os.urandom(5))
        surveytoken_row = models.SurveyToken(token=token, device_id=device_id, user=instance.user)
        instance.token = token
        surveytoken_row.device = instance

        # Don't forget to save.
        instance.save()
        surveytoken_row.save()

    @classmethod
    def configure(cls, device):
        instructions = """You should program the URL <tt>https://{main_domain}{post}</tt> to
        take this survey.  """.format(
            post=reverse_lazy('survey-take', kwargs=dict(token=device.surveydevice.token)),
            post_domain=settings.POST_DOMAIN,
            main_domain=settings.MAIN_DOMAIN,
            )
        return dict(qr=False,
                    raw_instructions=instructions)



class TestSurvey1(BaseSurvey):
    """This is a test survey."""
    @classmethod
    def get_survey(cls, data, device):
        questions = [
            ('to-bed',        Time('At what time did you go to bed last night? (please use 24h format)')),
            ('asleep',        Time('When did you approximately fall asleep? (please use 24h format)')),
            ('sleep-disturbs',Choice('After falling asleep, about how many times. did you wake up during the night?', (0, 1, 2, 3, 4, 5, more than 5 times))),
            ('woke-up-why',   Choice('If you woke up, what was the reason?', (Had to get up to use the bathroom, someone else woke me up (my child, pet, other...), had bad dreams, felt too cold/hot, coughing or snoring loudly, had pain, could not breath well, other))),
            ('time-awake',    Time('If you woke up, for how long were you awake during the night in total? (hh:mm)'),
            ('woke-up',       Time('At what time did you finally wake up? (please use 24h format)')),
            ('get-up',        Time('At what time did you get up? (please use 24h format)')),
            ('quality-sleep', Choice('How would you rate the quality of your sleep last night?', (1 - poor, 2, 3 - more or less, 4, 5 - excellent),
            ('rested-night',  Choice('Did you feel yourself rested after the night?', (1 - no, I feel very tired!, 2, 3 - indifferent, 4, 5 - yes, I feel very rested!))),
            ('sleep-alone',   Bool('Did you sleep alone?')),
        ]
        # Can do extra logic here
        survey_data = {'name': 'Test Survey 1',
                       'id': 1,
                       'questions':questions,
                   }

        return survey_data
#devices.register_device(TestSurvey1, "Test Survey #1")
