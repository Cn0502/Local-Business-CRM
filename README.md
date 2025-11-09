# Local-Business-CRM

A scalable order management system and web interface for local business services.

1.Create a Virtual Environment





On Windows (PowerShell)

py -m venv venv

.\\venv\\Scripts\\activate



On macOS / Linux

python3 -m venv venv

source venv/bin/activate





 You should see (venv) before your prompt when activated.



2\. Install Dependencies

pip install -r requirements.txt



3\. Create a .env File



In the same folder as manage.py, create a file named .env containing:



DJANGO\_SECRET\_KEY=your\_own\_random\_secret\_key\_here

DEBUG=True





To generate a key safely:



py -c "from django.core.management.utils import get\_random\_secret\_key; print(get\_random\_secret\_key())"



 Never commit .env to GitHub — it’s ignored for security.



python manage.py makemigrations

python manage.py migrate



python manage.py createsuperuser



python manage.py runserver





Open your browser at:

http://127.0.0.1:8000
 
Tony Write Test