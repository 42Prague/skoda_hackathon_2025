## Project made by Team Medici: "Traversity AI skillcoach"

### Getting Started

To run this project locally you will need to set your environment variables

1. Create a virtual environment inside the project by running `virtualenv venv` or `python3 -m venv myenv` in your terminal
3. Activate venv using `source venv/local/bin/activate` or `source venv/bin/activate`
4. Install all the needed packages from "requirements.txt" `pip install -r requirements.txt`
5. If some requirements are not installed, install them using `pip install <requirment>` (if pip not installed or not updated then install it or update it)
6. Add generated secret key into SECRET_KEY field in bugTrack/settings.py. Generate it using `python -c "import secrets; print(secrets.token_urlsafe(50))"`
7. Create .env file and add your values to it. Use env_template.txt as a mock up for creating .env
8. Make migrations by running `python manage.py migrate` in your terminal
9. Collect static files for icon and image `python3 manage.py collectstatic`
10. Run server using `python manage.py runserver` command (if already have your project ready and opened terminal again then activate terminal and run this command)
11. Write http://127.0.0.1:8000/ URL in your browser
12. Then register your account which you can find on the login page
13. Write URL that was send to you in a terminal
14. Now you can start exploring this application so enjoy the run!
