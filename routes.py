from app import app
from flask import render_template
from werkzeug.urls import url_parse
from flask import session, request, redirect

from utils import process_login, process_registration, process_logout
from utils import check_poll_validity, process_new_poll
from utils import Poll

@app.route('/')
def index():
    polls = [(str(i), f'kysely {i}') for i in range(4)]
    return render_template("index.html", polls=polls)


@app.route('/poll/<poll_id>')
def poll(poll_id):
    return "poll"


@app.route('/new_poll', methods=['GET', 'POST'])
def new_poll():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'GET':
        return render_template("new_poll.html")
    
    if request.method == 'POST':
        poll = Poll(session['user_id'],
                    request.form.get('poll_name'), 
                    request.form.get('poll_description'),
                    request.form.get('first_appointment_date'),
                    request.form.get('last_appointment_date'),
                    request.form.get('poll_end_date'),
                    request.form.get('poll_end_time'),
                    False)

        print(request.form)
        print(poll.name,
              poll.description, poll.first_date, poll.last_date, poll.end_date,
              poll.end_time)


        if not check_poll_validity(poll):
            #TODO some note about what was wrong
            print("not valid")
            return render_template("new_poll.html")

        print(poll)

        process_new_poll(poll)
        return redirect("/")






#TODO
#storing the 'login_redirect' in the session was a very bad idea
#what if the user visits the link, then does something else, 
#comes back to the site and logs in
#then they will be redirected to the link site

#how to login and then return to the same page?


#TODO give the message as a GET parameter?
@app.route('/login', methods=['GET', 'POST'])
def login():
    def redirect_to_next(default='/'):
        if 'login_redirect' not in session:
            return redirect(default)

        #if the redirect target is not a valid relative url
        url = session['login_redirect']
        del session['login_redirect']

        if not url or url_parse(url).netloc != '':
            return redirect(default)

        return redirect(url)

    if session.get('user_id', 0):
        return redirect_to_next(default='/');

    if request.method == 'GET':
        return render_template("login.html")

    elif request.method == 'POST':
        print("post request", request.form)

        if process_login(request.form['username'], request.form['password']):
            return redirect_to_next(default='/')

    return render_template('login.html', 
                           message='Kirjautuminen epäonnistui,yritä uudelleen')


@app.route('/logout')
def logout():
    process_logout()
    
    return render_template("logout.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    if request.method == 'POST':
        print("register: ", request.form)
        is_ok = process_registration(request.form['username'],
                                      request.form['password'])
        #after successful registration, automatically log the user in
        #and redirect to login
        if is_ok:
            process_login(request.form['username'],
                          request.form['password'])
            return redirect('/login') 

    return render_template("register.html",
                           message='Käyttäjätunnuksen luonti epäonnistui,yritä uudelleen')

@app.route('/invite/<url_id>', methods=['POST', 'GET'])
def invite(url_id):
    print('type of url_id', type(url_id))
    if not session.get('user_id', 0):
        session['login_redirect'] = "/invite/" + url_id
        return redirect('/login')

    invitation_type = get_invitation_type(url_id)
    #check if url_id is in database
    if invitation_type is None:
        return render_template('invalid_invitation.html')

    if request.method == 'GET':
        if invitation_type == 'poll_participant':
            #TODO think if the url_id should be in 'details'
            return render_template("confirm_poll.html",
                                   details=participant_invitation_by_url_id(url_id),
                                   url_id=url_id)

        if invitation_type == 'resource_owner':
            return render_template("confirm_resource.html",
                                   details=resource_invitation_by_url_id(url_id),
                                   url_id=url_id)
    if request.method == 'POST':
        print("user response: ", request.form['user_response'])
        if request.form["user_response"] == "yes":
            if invitation_type == 'poll_participant':
                apply_poll_invitation(url_id)
            if invitation_type == 'resource_owner':
                process_resource_invitation(url_id)
            #TODO add message
            return redirect('/')
        else:
            return redirect('/')


@app.route('/new_invitation', methods=['POST', 'GET'])
def new_invitation():
    if 'user_id' not in session:
        return redirect('/') 

    ok = process_new_invitation(request.form.get('invitation_type'),
                                request.form.get('poll_id'),
                                request.form.get('reservation_length'))

    print("new invitation request", request.form)
    print("ok? ", ok)
    if ok:
        return redirect('/poll/'+request.form.get('poll_id'))
    else:
        return redirect('/poll/'+request.form.get('poll_id'))
        pass
        #TODO
        #redirect to the poll with a message

