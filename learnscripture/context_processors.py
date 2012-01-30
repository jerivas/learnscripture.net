from .forms import SignupForm

def session_forms(request):
    # Use callables here to avoid overhead when not needed.  The template will
    # call them when used

    # We need different prefices on each form to avoid clashes with ids of
    # fields. Same prefix must be set in handlers.py

    def signup_form():
        return SignupForm(prefix="signup")

    return {'signup_form': signup_form}
