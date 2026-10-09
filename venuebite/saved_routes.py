"""HTTP validation/rendering only; saved browsing never calls analysis providers."""

import hmac
import secrets

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from venuebite.db import PersistenceError
from venuebite.services.comparison_service import EVIDENCE_LABELS, snapshot_sections
from venuebite.services.saved_site_service import FORM_FIELDS, SaveError
from venuebite.snapshots import SnapshotError


bp = Blueprint("saved", __name__)


def csrf_token():
    if "saved_csrf" not in session:
        session["saved_csrf"] = secrets.token_urlsafe(32)
    return session["saved_csrf"]


def valid_csrf():
    token = request.form.get("csrf_token", "")
    expected = session.get("saved_csrf", "")
    return len(request.form.getlist("csrf_token")) == 1 and bool(expected) and hmac.compare_digest(token, expected)


def service():
    return current_app.extensions["saved_site_service"]


def error_page(message, status):
    return render_template("saved_error.html", message=message, saved_workspace=True), status


@bp.get("/saved")
def index():
    try:
        listing = service().list()
    except PersistenceError as error:
        return error_page(str(error), 503)
    return render_template("saved_sites.html", listing=listing, saved_workspace=True)


@bp.post("/saved")
def save():
    if not valid_csrf():
        return error_page("This save form expired. Return to the analysis and try again.", 400)
    if any(len(request.form.getlist(field)) > 1 for field in (*FORM_FIELDS, "snapshot_token", "display_name", "location_label")):
        return error_page("Submit one completed analysis and saved name at a time.", 400)
    try:
        site, created = service().save(request.form.get("snapshot_token", ""), request.form.get("display_name", ""), request.form,
                                       location_label=request.form.get("location_label", ""))
    except SaveError as error:
        return error_page(str(error), 400)
    except (SnapshotError, PersistenceError) as error:
        return error_page(str(error), 503)
    flash("Site saved." if created else "This analysis snapshot is already saved; no duplicate was created.", "success")
    return redirect(url_for("saved.detail", site_id=site.id), code=303)


@bp.get("/saved/<site_id>")
def detail(site_id):
    try:
        site = service().get(site_id)
        if site is None:
            return error_page("This saved site was deleted or does not exist.", 404)
    except SaveError as error:
        return error_page(str(error), 400)
    except SnapshotError as error:
        return error_page(str(error), 422)
    except PersistenceError as error:
        return error_page(str(error), 503)
    return render_template("saved_detail.html", site=site, sections=snapshot_sections(site.snapshot), saved_workspace=True)


@bp.get("/saved/<site_id>/delete-confirmation")
def delete_confirmation(site_id):
    try:
        site = service().get(site_id)
        if site is None:
            flash("That saved site is already absent.", "notice")
            return redirect(url_for("saved.index"), code=303)
    except (SaveError, SnapshotError) as error:
        return error_page(str(error), 400)
    except PersistenceError as error:
        return error_page(str(error), 503)
    return render_template("saved_delete.html", site=site, saved_workspace=True)


@bp.post("/saved/<site_id>/delete")
def delete(site_id):
    if not valid_csrf() or request.form.get("confirm") != "delete":
        return error_page("Confirm deletion using the current saved-site confirmation form.", 400)
    try:
        deleted = service().delete(site_id)
    except SaveError as error:
        return error_page(str(error), 400)
    except PersistenceError as error:
        return error_page(str(error), 503)
    flash("Site deleted." if deleted else "That saved site is already absent.", "success")
    return redirect(url_for("saved.index"), code=303)


@bp.get("/compare")
def compare():
    try:
        listing = service().list()
        selected = request.args.getlist("site_id")
        comparison = None
        message = ""
        status = 200
        if selected:
            try:
                comparison = current_app.extensions["comparison_service"].compare(selected)
            except (SaveError, SnapshotError) as error:
                message, status = str(error), 400
        valid_selection = {str(site.id) for site in listing.sites}
        if not selected and request.args.get("pick") in valid_selection:
            selected = [request.args["pick"]]
        selected = [value for value in selected if value in valid_selection][:4]
        return render_template("compare.html", listing=listing, comparison=comparison, selected=selected,
                               comparison_error=message, saved_workspace=True), status
    except PersistenceError as error:
        return error_page(str(error), 503)


@bp.app_context_processor
def saved_context():
    return {"saved_csrf_token": csrf_token, "evidence_labels": EVIDENCE_LABELS}
