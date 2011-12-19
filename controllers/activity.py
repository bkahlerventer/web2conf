#############################################
# activities (activity proposal)
#############################################

# we are not in default controller, change it at crud
if not request.function in ('accepted', 'propossed', 'ratings', 'vote'):
    crud=Crud(globals(),db)
    crud.settings.controller='activity'

@auth.requires_login()
def proposed():
    activities=db(db.activity.id>0).select(orderby=db.activity.title)
    rows = db(db.review.created_by==auth.user.id).select()
    reviews = dict([(row.activity_id, row) for row in rows])
    d = dict(activities=activities, reviews=reviews)
    return response.render(d)

@auth.requires(auth.has_membership(role='reviewer') or TODAY_DATE>REVIEW_DEADLINE_DATE)
def ratings():
    query = (db.review.activity_id==db.activity.id) & (db.auth_user.id==db.activity.created_by)
    avg = db.review.rating.sum() / db.review.rating.count()
    ratings=db(query).select(
        db.activity.ALL,
        db.auth_user.ALL,
        db.review.rating.sum(), 
        db.review.rating.count(), 
        avg, 
        groupby=(db.activity.ALL,),
        orderby=~avg)
    
    votes = {}
    for k,item in enumerate(TUTORIALS_LIST):
        m=db(db.auth_user.tutorials.like('%%|%s|%%'%item)).count()
        votes[item] = m
                
    ratings = sorted(ratings, key=lambda row: (row["SUM(review.rating)"] / float(row["COUNT(review.rating)"]), row["COUNT(review.rating)"]), reverse=True)     
    d = dict(ratings=ratings, votes=votes, levels=ACTIVITY_LEVEL_HINT)
    return response.render(d)

@auth.requires_login()
def vote():

    rows = db(db.activity.id>=1).select(
            db.activity.id, 
            db.activity.title, 
            db.activity.authors, 
            db.activity.level, 
            db.activity.abstract,
            db.activity.categories, 
            orderby=db.activity.title)
    
    activities = {}
    
    fields = []
    for row in rows:
        activities[row.id] = row.title
        fields.append(LI(
            INPUT(_name='check.%s' % row.id, 
                  _type="checkbox", 
                  value=(auth.user.tutorials and row.title in auth.user.tutorials) and "on" or "",
                  ),
            LABEL(B(row.title), " ",  
                  ACTIVITY_LEVEL_HINT[row.level],
                  I(" %s (%s): " % (', '.join(row.categories or []), row.authors)), row.abstract,
                  _for='check.%s' % row.id),
            ))
    
    form = FORM(UL(fields, INPUT(_type="submit"), _class="checklist"))
        
    selected = []
    if form.accepts(request.vars, session):
        session.flash = T('Voto Aceptado!')
        for var in form.vars.keys():
            activity_id = "." in var and int(var.split(".")[1]) or None
            val = form.vars[var]
            if val == 'on':
                selected.append(activities[activity_id])
        auth.user.update(tutorials=selected)
        db(db.auth_user.id==auth.user.id).update(tutorials=selected)
        db.commit()
        redirect(URL(c="default", f="index"))

    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form, levels=ACTIVITY_LEVEL_HINT, message=db.auth_user.tutorials.comment)

@cache(request.env.path_info,time_expire=60,cache_model=cache.ram)
def accepted():
    db.activity['represent']=lambda activity: A('%s by %s' % (activity.title,activity.authors),
       _href=URL(r=request,f='activity_info',args=[activity.id]))
    query=(db.activity.status=='accepted')&(db.auth_user.id==db.activity.created_by)
    if request.args:
        query &=  db.activity.id==request.args[0]
    rows=db(query).select(orderby=db.activity.title)
    attachments=db(db.attachment.id>0).select()     
    attachs = {}
    for attach in attachments:
        attachs.setdefault(attach.activity_id, []).append(attach) 
    d = dict(rows=rows,attachs=attachs)
    return response.render(d)
    
@auth.requires_login()
def propose():
    if request.args:
        duration = ACTIVITY_DURATION.get(request.args[0])
        if duration is not None:
            db.activity.duration.default = duration
            db.activity.type.default = request.args[0]
            db.activity.duration.writable = False
            db.activity.type.writable = False
                
    insert_author = lambda form: db.author.insert(user_id=auth.user_id,activity_id=form.vars.id)
    return dict(form=crud.create(db.activity, 
                                 next='display/[id]', 
                                 onaccept=insert_author))

@auth.requires(auth.has_membership(role='manager') or (user_is_author() and TODAY_DATE<PROPOSALS_DEADLINE_DATE))
def update():
    if not db(db.activity.created_by==auth.user.id and db.activity.id==request.args[0]).count():
        redirect(URL(r=reuqest,f='index'))
    form=crud.update(db.activity, request.args[0],
                     next='display/[id]',
                     ondelete=lambda form: redirect(URL(r=request,f='index')))
    return dict(form=form)

@auth.requires(auth.has_membership(role='manager') or user_is_author() or auth.has_membership(role='reviewer'))
def display():
    activity_id=request.args[0]
    rows = db(db.activity.id==activity_id).select()
    activity = rows[0]
    item=crud.read(db.activity,activity_id)
    comments=db(db.comment.activity_id==activity_id).select()
    attachments=db(db.attachment.activity_id==activity_id).select()
    query = db.review.activity_id==activity_id
    if not auth.has_membership(role='manager') and TODAY_DATE<REVIEW_DEADLINE_DATE:
        query &= db.review.created_by==auth.user.id
    reviews=db(query).select()
    return dict(activity_id=activity_id,activity=activity,item=item,reviews=reviews,attachments=attachments,comments=comments)


@auth.requires(auth.has_membership(role='reviewer') or activity_is_accepted())
def info():
    activity_id=request.args[0]
    item=crud.read(db.activity,activity_id)
    return dict(item=item)

@auth.requires(auth.has_membership(role='manager')  or auth.has_membership(role='reviewer') or user_is_author())
def comment(): 
    activity = db(db.activity.id==request.args[0]).select()[0]
    db.comment.activity_id.default=activity.id
    form=crud.create(db.comment, 
                     next=URL(r=request,f='display',args=activity.id))
    return dict(activity=activity,form=form)

@auth.requires(auth.has_membership(role='reviewer') or user_is_author())
def attach(): 
    activity = db(db.activity.id==request.args[0]).select()[0]
    db.attachment.activity_id.default=activity.id
    if len(request.args)>1:
        attachs = db((db.attachment.activity_id==activity.id)&(db.attachment.id==request.args[1])).select()
    else:
        attachs = None
    if attachs:
        form=crud.update(db.attachment, attachs[0].id,
                         next=URL(r=request,f='display',args=activity.id),
                         ondelete=lambda form: redirect(URL(r=request,c='default',f='index')))
    else:
        form=crud.create(db.attachment, 
                         next=URL(r=request,f='display',args=activity.id))
    return dict(activity=activity,form=form)

@auth.requires(auth.has_membership(role='reviewer') and not user_is_author() and TODAY_DATE<REVIEW_DEADLINE_DATE)
def review(): 
    activity = db(db.activity.id==request.args[0]).select()[0]
    reviews = db((db.review.activity_id==activity.id)&(db.review.created_by==auth.user_id)).select()
    if reviews:
        form=crud.update(db.review, reviews[0].id,
                         next=URL(r=request,f='proposed'),
                         ondelete=lambda form: redirect(URL(r=request,c='default',f='index')))
    else:
        db.review.activity_id.default=activity.id
        form=crud.create(db.review, 
                         next=URL(r=request,f='proposed'))
    return dict(activity=activity,form=form)


@auth.requires(auth.has_membership(role='manager') or user_is_author())
def confirm(): 
    activity_id = request.args[0]
    db(db.activity.id==activity_id).update(confirmed=True)
    session.flash = T("Activity %s Confirmed. Thank you!" % (db.activity[activity_id].title))
    redirect(URL(r=request,f='display',args=activity_id))

@auth.requires(auth.has_membership(role='manager') or user_is_author())
def add_author(): 
    activity_id = request.args[0]
    # for privacy, do not list users that didn't want to make his attendance public
    delegates = db(db.auth_user.include_in_delegate_listing==True).select(db.auth_user.id, db.auth_user.first_name, db.auth_user.last_name)
    delegates = [(user.id, "%(last_name)s, %(first_name)s" % user) for user in delegates]
    delegates.sort(key=lambda x: x[1].upper())
    form = SQLFORM.factory(
        Field("activity_id", db.activity, label=T("Activity"), writable=False,
              requires=IS_IN_DB(db, db.activity, "%(title)s"),
              represent=lambda x: (db.activity[x].title),
              default=activity_id),
        Field("user_id", db.auth_user, label=T("Author"),
              requires=IS_IN_SET(delegates),),
        )
    if form.accepts(request.vars, session):
        user_id = form.vars.user_id
        q = db.author.activity_id==activity_id
        q &= db.author.user_id==user_id
        if not db(q).count():
            db.author.insert(activity_id=activity_id, user_id=user_id)
            session.flash = "Author added!"
        else:
            session.flash = "Author already added!"
        redirect(URL(r=request,f='display',args=activity_id))
    elif form.errors:
        request.flash = "Form has errors"
    return dict(form=form)
    
@cache(request.env.path_info,time_expire=60,cache_model=cache.ram)
def speakers():
    s=db(db.auth_user.speaker==True)
    authors=s.select(db.auth_user.ALL,
                  orderby=db.auth_user.last_name|db.auth_user.first_name)
    rows = db((db.activity.id==db.author.activity_id)&(db.activity.status=='accepted')).select()
    activities_by_author = {}
    for row in rows:
        activities_by_author.setdefault(row.author.user_id, []).append(row.activity) 
    return dict(authors=authors, activities_by_author=activities_by_author)

def download(): 
    query = (db.attachment.file==request.args[0])&(db.activity.id==db.attachment.activity_id)
    activity = db(query).select(db.activity.id,db.activity.status)[0]
    if activity.status=='accepted' or auth.has_membership(role='reviewer') or user_is_author(activity.id):
        return response.download(request,db)
    raise HTTP(501)