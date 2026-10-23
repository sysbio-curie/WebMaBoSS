from django.contrib.auth.models import User

from .project import Project

# The account of the anonymous users, who share the demo project
GUEST_USERNAME = "____GUEST____"

def create_guest_account():

    try:
        guest_account = User.objects.get(username=GUEST_USERNAME)
        return guest_account    

    except User.DoesNotExist as e:
        guest_account = User(
            username=GUEST_USERNAME,
        )
        guest_account.save()
        
        default_project = Project.objects.get(user=guest_account)
        default_project.name = "Demo models"
        default_project.save()
        
        return guest_account    


def clean_guest_account():
    """
    Deletes the simulations of the anonymous users older than a day (DEMO_KEPT), a batch at a time. Done by the
    maintenance job (manage.py maintenance), and when an anonymous user starts a simulation (without that job).
    """
    # Imported here : the monitoring imports the models
    from api.monitoring import cleanup
    return cleanup("demo")
