# Import services here
from app.services.auth_service import check_login, login_required, hash256
from app.services.customer_service import get_customers_service, get_customer_service, add_customer_service, update_customer_service, delete_customer_service, search_customers_service, initialize_customer_db
from app.services.project_service import get_projects_service, get_project_service, add_project_service, update_project_service, delete_project_service, initialize_project_db
from app.services.raman_service import raman_plot_in_range, generate_plot
from app.services.streaming_service import start_streaming
from app.services.optimization_service import process_optimization_data, run_optimization
from app.services.contour_service import process_form_data
from app.services.upload_service import upload_csv_service, send_csv_to_another_vm
from app.services.query_service import executive_query
from app.services.producer_service import produce_data, consume_kafka
from app.services.hash_service import hash256 