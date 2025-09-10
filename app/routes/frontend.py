"""
Frontend routes and static file handling for demo pages
"""

import os
from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.util.log import get_logger

logger = get_logger(__name__)


def setup_frontend_routes(app: FastAPI) -> None:
    """
    Set up frontend routes and static file serving for demo pages.

    This function configures:
    - Static file mounting for CSS, JS, and other assets
    - Route handlers for serving HTML pages
    - Proper path resolution for the view directory

    Args:
        app: FastAPI application instance
    """
    # Get the view directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    static_dir = os.path.join(project_root, "view")
    user_dir = os.path.join(static_dir, "user")
    admin_dir = os.path.join(static_dir, "admin")

    logger.info(f"Looking for static directory at: {static_dir}")

    if not os.path.exists(static_dir):
        logger.warning(f"Static directory not found: {static_dir}")
        return

    try:
        # Mount CSS and JS directories specifically
        css_dir = os.path.join(static_dir, "css")
        js_dir = os.path.join(static_dir, "js")

        if os.path.exists(css_dir):
            app.mount("/css", StaticFiles(directory=css_dir), name="css")
            logger.info(f"Mounted CSS directory: {css_dir}")
        else:
            logger.warning(f"CSS directory not found: {css_dir}")

        if os.path.exists(js_dir):
            app.mount("/js", StaticFiles(directory=js_dir), name="js")
            logger.info(f"Mounted JS directory: {js_dir}")
        else:
            logger.warning(f"JS directory not found: {js_dir}")

        # Mount images directory
        images_dir = os.path.join(static_dir, "images")
        if os.path.exists(images_dir):
            app.mount("/images", StaticFiles(directory=images_dir), name="images")
            logger.info(f"Mounted images directory: {images_dir}")
        else:
            logger.warning(f"Images directory not found: {images_dir}")

        # Mount the main static directory (root) plus user/admin sub-folders if present
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        # Unified mount for whole view tree to give a stable absolute path
        if "view" not in {m.name for m in app.router.routes if hasattr(m, "name")}:
            app.mount("/view", StaticFiles(directory=static_dir), name="view")
            logger.info(f"Mounted /view alias to: {static_dir}")
        logger.info(f"Mounted static base directory: {static_dir}")

        if os.path.exists(user_dir):
            app.mount(
                "/user-static", StaticFiles(directory=user_dir), name="user_static"
            )
            logger.info(f"Mounted user directory: {user_dir}")
        else:
            logger.warning(f"User directory not found: {user_dir}")

        if os.path.exists(admin_dir):
            app.mount(
                "/admin-static", StaticFiles(directory=admin_dir), name="admin_static"
            )
            logger.info(f"Mounted admin directory: {admin_dir}")
        else:
            logger.warning(f"Admin directory not found: {admin_dir}")

        # Add route handlers for HTML pages & partials
        _add_frontend_routes(app, static_dir)

        logger.info("Frontend routes and static files configured successfully")

    except Exception as e:
        logger.error(f"Error setting up frontend routes: {e}")
        raise


def _add_frontend_routes(app: FastAPI, static_dir: str) -> None:
    """
    Add route handlers for serving HTML pages.

    Args:
        app: FastAPI application instance
        static_dir: Path to the static files directory
    """

    @app.get("/")
    async def read_root():
        """Serve main page (login)."""
        login_file = os.path.join(static_dir, "user", "login.html")
        if os.path.exists(login_file):
            return FileResponse(login_file)
        # fallback old path
        legacy_login = os.path.join(static_dir, "login.html")
        if os.path.exists(legacy_login):
            logger.warning("Using legacy login.html at root of view directory")
            return FileResponse(legacy_login)
        logger.error(f"Login file not found in expected paths: {login_file}")
        return {"error": "Login page not found"}

    @app.get("/login")
    async def login_page():
        """Serve the login page."""
        login_file = os.path.join(static_dir, "user", "login.html")
        if os.path.exists(login_file):
            return FileResponse(login_file)
        legacy_login = os.path.join(static_dir, "login.html")
        if os.path.exists(legacy_login):
            logger.warning("Using legacy login.html (old path)")
            return FileResponse(legacy_login)
        logger.error(f"Login file not found: {login_file}")
        return {"error": "Login page not found"}

    @app.get("/home")
    async def home_page():
        """Serve the user home/dashboard page."""
        home_file = os.path.join(static_dir, "user", "home.html")
        if os.path.exists(home_file):
            return FileResponse(home_file)
        legacy_home = os.path.join(static_dir, "home.html")
        if os.path.exists(legacy_home):
            logger.warning("Using legacy home.html (old path)")
            return FileResponse(legacy_home)
        logger.error(f"Home file not found: {home_file}")
        return {"error": "Home page not found"}

    @app.get("/register")
    async def register_page():
        """Serve the registration page."""
        register_file = os.path.join(static_dir, "user", "register.html")
        if os.path.exists(register_file):
            return FileResponse(register_file)
        legacy_register = os.path.join(static_dir, "register.html")
        if os.path.exists(legacy_register):
            logger.warning("Using legacy register.html (old path)")
            return FileResponse(legacy_register)
        logger.error(f"Register file not found: {register_file}")
        return {"error": "Register page not found"}

    @app.get("/profile")
    async def profile_page():
        """Serve the user profile page."""
        profile_file = os.path.join(static_dir, "user", "profile.html")
        if os.path.exists(profile_file):
            return FileResponse(profile_file)
        logger.error(f"Profile file not found: {profile_file}")
        return {"error": "Profile page not found"}

    @app.get("/universities")
    async def universities_page():
        """Serve the universities listing page."""
        uni_file = os.path.join(static_dir, "user", "university.html")
        if os.path.exists(uni_file):
            return FileResponse(uni_file)
        logger.error(f"University listing file not found: {uni_file}")
        return {"error": "Universities page not found"}

    @app.get("/programs")
    async def programs_page():
        """Serve the programs listing page."""
        program_file = os.path.join(static_dir, "user", "program.html")
        if os.path.exists(program_file):
            return FileResponse(program_file)
        logger.error(f"Program listing file not found: {program_file}")
        return {"error": "Programs page not found"}

    @app.get("/contact")
    async def contact_page():
        """Serve the contact page."""
        contact_file = os.path.join(static_dir, "user", "contact.html")
        if os.path.exists(contact_file):
            return FileResponse(contact_file)
        logger.error(f"Contact file not found: {contact_file}")
        return {"error": "Contact page not found"}

    @app.get("/rankings")
    async def rankings_page():
        """Serve the rankings (top ranked programs) page."""
        ranking_file = os.path.join(static_dir, "user", "ranking.html")
        if os.path.exists(ranking_file):
            return FileResponse(ranking_file)
        logger.error(f"Ranking file not found: {ranking_file}")
        return {"error": "Rankings page not found"}

    @app.get("/program-detail")
    async def program_detail_page():
        """Serve the program detail page."""
        program_detail_file = os.path.join(static_dir, "user", "program-detail.html")
        if os.path.exists(program_detail_file):
            return FileResponse(program_detail_file)
        logger.error(f"Program detail file not found: {program_detail_file}")
        return {"error": "Program detail page not found"}

    @app.get("/application")
    async def application_page():
        """Serve the application form page."""
        application_file = os.path.join(static_dir, "user", "application.html")
        if os.path.exists(application_file):
            return FileResponse(application_file)
        logger.error(f"Application file not found: {application_file}")
        return {"error": "Application page not found"}

    @app.get("/my-applications")
    async def my_applications_page():
        """Serve the my applications page."""
        my_applications_file = os.path.join(static_dir, "user", "my_applications.html")
        if os.path.exists(my_applications_file):
            return FileResponse(my_applications_file)
        logger.error(f"My applications file not found: {my_applications_file}")
        return {"error": "My applications page not found"}

    # Add .html extensions as well for direct access
    @app.get("/login.html")
    async def login_html():
        return await login_page()

    @app.get("/home.html")
    async def home_html():
        return await home_page()

    @app.get("/register.html")
    async def register_html():
        return await register_page()

    @app.get("/profile.html")
    async def profile_html():
        return await profile_page()

    @app.get("/universities.html")
    async def universities_html():
        return await universities_page()

    @app.get("/programs.html")
    async def programs_html():
        return await programs_page()

    @app.get("/contact.html")
    async def contact_html():
        return await contact_page()

    @app.get("/rankings.html")
    async def rankings_html():
        return await rankings_page()

    @app.get("/program-detail.html")
    async def program_detail_html():
        return await program_detail_page()

    @app.get("/application.html")
    async def application_html():
        return await application_page()

    @app.get("/my-applications.html")
    async def my_applications_html():
        return await my_applications_page()

    # Admin specific pages
    @app.get("/admin/login")
    async def admin_login_page():
        admin_login = os.path.join(static_dir, "admin", "login.html")
        if os.path.exists(admin_login):
            logger.info("Serving admin login page")
            return FileResponse(admin_login)
        logger.error(f"Admin login file not found: {admin_login}")
        return {"error": "Admin login page not found"}

    @app.get("/admin/login.html")
    async def admin_login_html():
        return await admin_login_page()

    @app.get("/admin/dashboard")
    async def admin_dashboard_placeholder():
        dashboard = os.path.join(static_dir, "admin", "dashboard.html")
        if os.path.exists(dashboard):
            logger.info("Serving admin dashboard page")
            return FileResponse(dashboard)
        logger.error(f"Admin dashboard file not found: {dashboard}")
        return {"message": "Admin dashboard page not found"}

    @app.get("/admin/register")
    async def admin_register_page():
        admin_register = os.path.join(static_dir, "admin", "register.html")
        if os.path.exists(admin_register):
            logger.info("Serving admin registration page")
            return FileResponse(admin_register)
        logger.error(f"Admin register file not found: {admin_register}")
        return {"error": "Admin registration page not found"}

    @app.get("/admin/register.html")
    async def admin_register_html():
        return await admin_register_page()

    @app.get("/admin/users")
    async def admin_users_page():
        admin_users = os.path.join(static_dir, "admin", "user.html")
        if os.path.exists(admin_users):
            logger.info("Serving admin users management page")
            return FileResponse(admin_users)
        logger.error(f"Admin users page not found: {admin_users}")
        return {"error": "Admin users page not found"}

    @app.get("/admin/users.html")
    async def admin_users_html():
        return await admin_users_page()

    @app.get("/admin/regions")
    async def admin_regions_page():
        region_page = os.path.join(static_dir, "admin", "region.html")
        if os.path.exists(region_page):
            logger.info("Serving admin regions management page")
            return FileResponse(region_page)
        logger.error(f"Admin region file not found: {region_page}")
        return {"error": "Admin regions page not found"}

    @app.get("/admin/regions.html")
    async def admin_regions_html():
        return await admin_regions_page()

    @app.get("/admin/universities")
    async def admin_universities_page():
        uni_page = os.path.join(static_dir, "admin", "university.html")
        if os.path.exists(uni_page):
            logger.info("Serving admin universities management page")
            return FileResponse(uni_page)
        logger.error(f"Admin universities file not found: {uni_page}")
        return {"error": "Admin universities page not found"}

    @app.get("/admin/universities.html")
    async def admin_universities_html():
        return await admin_universities_page()

    @app.get("/admin/programs")
    async def admin_programs_page():
        program_page = os.path.join(static_dir, "admin", "program.html")
        if os.path.exists(program_page):
            logger.info("Serving admin programs management page")
            return FileResponse(program_page)
        logger.error(f"Admin program file not found: {program_page}")
        return {"error": "Admin programs page not found"}

    @app.get("/admin/programs.html")
    async def admin_programs_html():
        return await admin_programs_page()

    @app.get("/admin/applications")
    async def admin_applications_page():
        app_page = os.path.join(static_dir, "admin", "application.html")
        if os.path.exists(app_page):
            logger.info("Serving admin applications management page")
            return FileResponse(app_page)
        logger.error(f"Admin applications file not found: {app_page}")
        return {"error": "Admin applications page not found"}

    @app.get("/admin/applications.html")
    async def admin_applications_html():
        return await admin_applications_page()

    @app.get("/admin/user_application")
    async def admin_user_application_page():
        ua_page = os.path.join(static_dir, "admin", "user_application.html")
        if os.path.exists(ua_page):
            logger.info("Serving admin user application detail page")
            return FileResponse(ua_page)
        logger.error(f"Admin user application detail page not found: {ua_page}")
        return {"error": "Admin user application detail page not found"}

    @app.get("/admin/user_application.html")
    async def admin_user_application_html():
        return await admin_user_application_page()

    # Add alias route with dash for backward compatibility
    @app.get("/admin/user-application")
    async def admin_user_application_dash():
        return await admin_user_application_page()

    @app.get("/admin/user-application.html")
    async def admin_user_application_dash_html():
        return await admin_user_application_page()

    # Add specific routes for partials
    @app.get("/user/partials/layout.html")
    async def user_layout_partial():
        """Serve the user layout partial."""
        layout_file = os.path.join(static_dir, "user", "partials", "layout.html")
        if os.path.exists(layout_file):
            return FileResponse(layout_file)
        logger.error(f"Layout partial not found: {layout_file}")
        return {"error": "Layout partial not found"}

    @app.get("/view/user/partials/layout.html")
    async def user_layout_partial_view():
        """Serve the user layout partial with view prefix."""
        return await user_layout_partial()

    @app.get("/static/user/partials/layout.html")
    async def user_layout_partial_static():
        """Serve the user layout partial with static prefix."""
        return await user_layout_partial()

    # --- Admin partials (new) ---
    @app.get("/admin/partials/layout.html")
    async def admin_layout_partial():
        """Serve the admin layout partial (authoritative path)."""
        layout_file = os.path.join(static_dir, "admin", "partials", "layout.html")
        if os.path.exists(layout_file):
            return FileResponse(layout_file)
        logger.error(f"Admin layout partial not found: {layout_file}")
        return {"error": "Admin layout partial not found"}

    # Keep alias routes but ensure they delegate only to the authoritative handler
    @app.get("/view/admin/partials/layout.html")
    async def admin_layout_partial_view():
        return await admin_layout_partial()

    @app.get("/static/admin/partials/layout.html")
    async def admin_layout_partial_static():
        return await admin_layout_partial()

    @app.get("/admin-static/partials/layout.html")
    async def admin_layout_partial_admin_static():
        return await admin_layout_partial()


# Router for any additional frontend API endpoints if needed
router = APIRouter()


@router.get("/frontend/status")
async def frontend_status():
    """
    Get the status of the frontend setup.

    Returns:
        dict: Status information about frontend configuration
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    static_dir = os.path.join(project_root, "view")
    user_dir = os.path.join(static_dir, "user")
    admin_dir = os.path.join(static_dir, "admin")

    css_dir = os.path.join(static_dir, "css")
    js_dir = os.path.join(static_dir, "js")

    status = {
        "static_dir_exists": os.path.exists(static_dir),
        "static_dir_path": static_dir,
        "user_dir_exists": os.path.exists(user_dir),
        "admin_dir_exists": os.path.exists(admin_dir),
        "css_dir_exists": os.path.exists(css_dir),
        "js_dir_exists": os.path.exists(js_dir),
        "files": {
            "user/login.html": os.path.exists(os.path.join(user_dir, "login.html")),
            "user/home.html": os.path.exists(os.path.join(user_dir, "home.html")),
            "user/register.html": os.path.exists(
                os.path.join(user_dir, "register.html")
            ),
            "user/partials/layout.html": os.path.exists(
                os.path.join(user_dir, "partials", "layout.html")
            ),
            "legacy_login.html": os.path.exists(os.path.join(static_dir, "login.html")),
            "legacy_home.html": os.path.exists(os.path.join(static_dir, "home.html")),
            "legacy_register.html": os.path.exists(
                os.path.join(static_dir, "register.html")
            ),
            "style.css": os.path.exists(os.path.join(css_dir, "style.css")),
            "index.js": os.path.exists(os.path.join(js_dir, "index.js")),
        },
    }

    return status
