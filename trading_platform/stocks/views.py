from django.shortcuts import render, redirect, get_object_or_404
from . import utils as pc
from datetime import datetime
import requests
from django.views.generic import ListView, DeleteView
from.models import Position
from Users.forms import CreateEquityPosition
from django.contrib.auth.models import User
from django.db.models import Sum, F
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse

def home(request):
    return render(request, 'stocks/index.html', {"title": "Home"})


def search_stocks(request):
    search = request.POST.get("searched_stock")
    if not search:
        message = "You submitted an empty form. Please try again."
        return render(request, "stocks/search_stocks.html", {'message': message})
    elif request.method == 'POST':
        message = f"Search results for {search}"
        matches_list = []
        searched_stock = request.POST['searched_stock']
        url = 'https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={}&apikey=9XLJ9WHT2OOGDEOC'.format(searched_stock)
        response = requests.get(url)
        matches = response.json()['bestMatches']
        for match in matches:
            latest_price = pc.get_stock_price(match['1. symbol'])
            stock_dict = {
            'Symbol' : match['1. symbol'],
            'Name': match['2. name'],
            'Region': match['4. region'],
            'Price': latest_price,
            }
            matches_list.append(stock_dict)
        return render(request, 'stocks/search_stocks.html', {'matches': matches_list, 'searched_stock': searched_stock, 'message': message, 'json':matches, "title": "Search companies"})
    else:
        return render(request, 'stocks/search_stocks.html', {"title": "Search companies"})


def searched_stock(request, ticker):
    ticker = ticker
    chart = pc.make_graph(ticker, datetime.today().strftime("%Y%m%d"), "date")
    summary = pc.get_individual_stock_details(ticker)
    articles = pc.get_latest_news(ticker,5)
    context = {
        "ticker": ticker,
        "summary": summary,
        "chart":chart,
        "articles": articles,
        "title": "Company info"

    }
    return render(request, "stocks/stock.html", context)



def new_equity_position(request, ticker, price):
    if request.method == "POST":
        form = CreateEquityPosition(request.POST, initial={"symbol": ticker, "price": price})
        ticker = ticker
        price = price
        if form.is_valid():
            user=request.user
            amount = form.cleaned_data.get("amount_invested")
            new_position = Position(user=user, symbol=ticker, price=price, amount_invested=amount)
            new_position.save()
            messages.success(request, f"{ticker} was added to your portfolio!")
            return redirect("home")
    form = CreateEquityPosition(initial={"symbol": ticker, "price": price})
    return render(request, "stocks/position_form.html", {"form":form, "title": "Add position"})


class UserPositionListView(ListView):
    model = Position
    template_name = 'stocks/user_position.html'

    context_object_name = 'positions'

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get("username"))
        return Position.objects.filter(user=user).order_by('symbol')


    def get_context_data(self, **kwargs):
        user = get_object_or_404(User, username=self.kwargs.get("username"))
        context = super(UserPositionListView, self).get_context_data(**kwargs)


        context['total'] = Position.objects.filter(user=user).aggregate(Sum('amount_invested')).get('amount_invested__sum')
        context['total_shares_per_equity'] = Position.objects.filter(user=user).values('symbol').order_by('symbol').annotate(number_shares=Sum(F('amount_invested')/F('price')))
        context['amount_invested_per_equity'] = Position.objects.filter(user=user).values('symbol').order_by('symbol').annotate(total=Sum('amount_invested'))
        return context


class UserPositionDelete(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Position
    success_url = '/'

    def test_func(self):
        position = self.get_object()
        if self.request.user == position.user:
            return True
        return False

    def get_success_url(self):
        messages.success(self.request, "Position was deleted successfully")
        return reverse("home")
