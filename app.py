"""
Help Desk Ticket Tracker - Main Flask Application
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Ticket, TroubleshootingNote
from sqlalchemy import func, or_

ALLOWED_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
ALLOWED_CATEGORIES = ['Hardware', 'Software', 'Network', 'Account Access', 'Other']
ALLOWED_STATUSES = ['Open', 'In Progress', 'Resolved', 'Closed']


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'dev-secret-key-change-this-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'tickets.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)

    register_routes(app)
    register_error_handlers(app)

    @app.context_processor
    def inject_global_vars():
        return {'current_year': datetime.utcnow().year}

    return app


def register_routes(app):

    @app.route('/')
    @app.route('/dashboard')
    def dashboard():
        total = Ticket.query.count()
        open_ = Ticket.query.filter_by(status='Open').count()
        in_progress = Ticket.query.filter_by(status='In Progress').count()
        resolved = Ticket.query.filter_by(status='Resolved').count()
        closed = Ticket.query.filter_by(status='Closed').count()

        recent = Ticket.query.order_by(Ticket.created_at.desc()).limit(5).all()

        priority_stats = db.session.query(Ticket.priority, func.count(Ticket.id)).group_by(Ticket.priority).all()
        category_stats = db.session.query(Ticket.category, func.count(Ticket.id)).group_by(Ticket.category).all()

        return render_template('dashboard.html',
                               total_tickets=total, open_tickets=open_,
                               in_progress_tickets=in_progress, resolved_tickets=resolved,
                               closed_tickets=closed, recent_tickets=recent,
                               priority_stats=priority_stats, category_stats=category_stats)

    @app.route('/tickets')
    def list_tickets():
        q = request.args.get('q', '').strip()
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        category = request.args.get('category', '')

        query = Ticket.query
        if q:
            try:
                query = query.filter((Ticket.id == int(q)) | 
                                     Ticket.title.ilike(f'%{q}%') | 
                                     Ticket.description.ilike(f'%{q}%'))
            except:
                query = query.filter(Ticket.title.ilike(f'%{q}%') | Ticket.description.ilike(f'%{q}%'))

        if status: query = query.filter_by(status=status)
        if priority: query = query.filter_by(priority=priority)
        if category: query = query.filter_by(category=category)

        tickets = query.order_by(Ticket.created_at.desc()).all()
        return render_template('tickets.html', tickets=tickets, search_query=q,
                               status_filter=status, priority_filter=priority, category_filter=category,
                               allowed_statuses=ALLOWED_STATUSES, allowed_priorities=ALLOWED_PRIORITIES,
                               allowed_categories=ALLOWED_CATEGORIES)

    @app.route('/tickets/new', methods=['GET', 'POST'])
    def create_ticket():
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            desc = request.form.get('description', '').strip()
            prio = request.form.get('priority', '')
            cat = request.form.get('category', '')

            if not title or not desc or prio not in ALLOWED_PRIORITIES or cat not in ALLOWED_CATEGORIES:
                flash('Please fill all required fields correctly.', 'danger')
                return render_template('create_ticket.html', allowed_priorities=ALLOWED_PRIORITIES,
                                       allowed_categories=ALLOWED_CATEGORIES)

            t = Ticket(title=title, description=desc, priority=prio, category=cat, status='Open')
            db.session.add(t)
            db.session.commit()
            flash(f'Ticket #{t.id} created!', 'success')
            return redirect(url_for('ticket_details', ticket_id=t.id))

        return render_template('create_ticket.html', allowed_priorities=ALLOWED_PRIORITIES,
                               allowed_categories=ALLOWED_CATEGORIES)

    @app.route('/tickets/<int:ticket_id>')
    def ticket_details(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        notes = TroubleshootingNote.query.filter_by(ticket_id=ticket_id).order_by(TroubleshootingNote.created_at.asc()).all()
        return render_template('ticket_details.html', ticket=ticket, notes=notes, allowed_statuses=ALLOWED_STATUSES)

    @app.route('/tickets/<int:ticket_id>/edit', methods=['GET', 'POST'])
    def edit_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        if request.method == 'POST':
            ticket.title = request.form.get('title', '').strip()
            ticket.description = request.form.get('description', '').strip()
            ticket.priority = request.form.get('priority', '')
            ticket.category = request.form.get('category', '')
            ticket.status = request.form.get('status', '')
            db.session.commit()
            flash('Ticket updated!', 'success')
            return redirect(url_for('ticket_details', ticket_id=ticket.id))
        return render_template('edit_ticket.html', ticket=ticket,
                               allowed_priorities=ALLOWED_PRIORITIES,
                               allowed_categories=ALLOWED_CATEGORIES,
                               allowed_statuses=ALLOWED_STATUSES)

    @app.route('/tickets/<int:ticket_id>/status', methods=['POST'])
    def update_status(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        new_status = request.form.get('status')
        if new_status in ALLOWED_STATUSES:
            ticket.status = new_status
            db.session.commit()
            flash(f'Status changed to {new_status}', 'success')
        return redirect(url_for('ticket_details', ticket_id=ticket_id))

    @app.route('/tickets/<int:ticket_id>/notes', methods=['POST'])
    def add_note(ticket_id):
        note_text = request.form.get('note', '').strip()
        if note_text:
            db.session.add(TroubleshootingNote(ticket_id=ticket_id, note=note_text))
            db.session.commit()
            flash('Note added!', 'success')
        return redirect(url_for('ticket_details', ticket_id=ticket_id))

    @app.route('/tickets/<int:ticket_id>/delete', methods=['POST'])
    def delete_ticket(ticket_id):
        ticket = Ticket.query.get_or_404(ticket_id)
        db.session.delete(ticket)
        db.session.commit()
        flash('Ticket deleted.', 'success')
        return redirect(url_for('list_tickets'))

    @app.route('/statistics')
    def statistics():
        total = Ticket.query.count()
        return render_template('statistics.html', total_tickets=total)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)