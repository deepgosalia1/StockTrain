import requests
import pandas as pd
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import *
from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as django_logout

API_KEY = '63XAFJTFC5HF4OE9'

def index_page(request):
    if(request.method=='GET' or (request.method=='POST' and 'refresh' in request.POST)):
        all_stocks=Stock.objects.all()
    if request.method=='POST' and 'search' in request.POST:
        filter=request.POST.get('filter','')
        all_stocks=Stock.objects.filter(name__startswith=filter)
    return render(request, 'stock/index.html', {'all_stocks':all_stocks})

def detail(request, stock_id):
    stock=get_object_or_404(Stock, id=stock_id)
    cp=requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol='+stock.symbol+'&interval=1min&apikey='+API_KEY)
    dict_cp=dict(cp.json())
    dict_cp=dict_cp['Time Series (1min)']
    ap=[]
    vol=[]
    for i in list(dict_cp.keys())[::2]:
        ap.append(float(dict_cp[i]["4. close"]))
        vol.append(float(dict_cp[i]["5. volume"]))
    current_price=dict_cp[list(dict_cp.keys())[0]]['4. close']
    dict_of_prices={}
    data=requests.get('https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol='+stock.symbol+'&apikey='+API_KEY)
    dict_of_prices=dict(data.json())
    date1=dict_of_prices['Time Series (Daily)'].keys()
    date=[]
    for x in date1:
        date.append(str(x))
    print(date)
    open=[]
    high=[]
    low=[]
    close=[]
    volume=[]
    for i in date:
        open.append(float(dict_of_prices['Time Series (Daily)'][i]["1. open"]))
        high.append(float(dict_of_prices['Time Series (Daily)'][i]["2. high"]))
        low.append(float(dict_of_prices['Time Series (Daily)'][i]["3. low"]))
        close.append(float(dict_of_prices['Time Series (Daily)'][i]["4. close"]))
        volume.append(float(dict_of_prices['Time Series (Daily)'][i]["5. volume"]))
    message=""
    if request.method=='POST' and 'add' in request.POST:
        if request.user.is_authenticated():
            watch = Watch(user=request.user, stock=stock)
            watch.save()
            message="Added To WatchList"
        else:
            message="Please Login to Continue"
            return redirect('/login')
    if request.method=='POST' and 'buy' in request.POST:
        if request.user.is_authenticated():
            quantity = int(request.POST.get('quantity', ''))
            profile = Profile.objects.get(user=request.user)
            x = float(current_price)*quantity
            if(profile.balance < x):
                message="Insufficient Balance"
            else:
                bought = Buy(user=request.user, stock=stock,quantity=quantity, price=float(current_price))
                bought.save()
                profile.balance = profile.balance-x
                profile.save()
                message="The Stock is Bought at price "+current_price+" with current balance = "+str(profile.balance)+"\nDeducted INR= "+str(x)
        else:
            message="Please Login to Continue"
            return redirect('/login')
    if request.method=='POST' and 'sell' in request.POST:
        if request.user.is_authenticated():
            quantity = int(request.POST.get('squantity', ''))
            q = quantity
            ast = Buy.objects.filter(user=request.user, stock=stock)
            tq = 0
            for i in ast:
                tq = tq + i.quantity
            if(tq>=quantity):
                profile = Profile.objects.get(user=request.user)
                profile.balance = profile.balance + quantity*float(current_price)
                profile.save()
                for i in ast:
                    if(quantity-i.quantity>=0):
                        quantity = quantity - i.quantity
                        i.delete()
                    else:
                        i.quantity = i.quantity - quantity
                        i.save()
                        quantity = 0
                        break
                message="Succesfully sold your "+ str(q)+" stocks. Added money "+str(quantity*float(current_price))+". Total Balance = "+str(profile.balance)+". Total Stocks Of Item Left: "+str(tq-q)
            else:
                message="Not enough Stock of this company. Owned Stocks = "+str(tq)
        else:
            message="Please Login to Continue"
            return redirect('/login')

    context={
        'stock': stock,
        'current_price': current_price,
        'date': date,
        'open': open,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
        'message': message,
        'ap': ap,
        'vol': vol
    }
    return render(request, 'stock/detail.html', context)

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        FirstName = request.POST.get('fname', '')
        LastName = request.POST.get('lname', '')
        email = request.POST.get('email', '')
        user = User.objects.create_user(username=username, email=email, first_name=FirstName, last_name=LastName)
        user.set_password(password)
        user.save()
        profile = Profile(user=user)
        profile.save()
        login(request, user)
        return redirect('/index')
    else:
        return render(request, 'stock/registration.html', {})

def login_user(request):
    if request.user.is_authenticated:
        user = request.user
        return redirect('/profile/%s' %user.id)
    else:
        if request.method == 'POST':
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    login(request, user)
                    return redirect('/profile/%s' %user.id)
                else:
                    error = 'Your account is disabled.'
                    return render(request, 'stock/login.html', {'error': error})
            else:
                error = 'Incorrect Username or Password'
                return render(request, 'stock/login.html', {'error': error})
        else:
            return render(request, 'stock/login.html', {})

def logout(request):
    django_logout(request)
    return redirect('/login')

@login_required(login_url='/login/')
def profile(request, user_id):
   user = get_object_or_404(User, pk=user_id)
   list_of_stocks = user.entries.all()
   bought_stocks = user.bentries.all()
   profile = Profile.objects.get(user=user)
   current_balance = profile.balance
   return render(request, 'stock/profile.html', {'user': user, 'stocks': list_of_stocks, 'cb': current_balance, 'bs': bought_stocks})
