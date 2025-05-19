from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import User, Listing, Category, Bid, Comment

from decimal import Decimal


def index(request):
    listings = Listing.objects.filter(active=True)
    listings_with_bids = []
    for listing in listings:
        current_bid = listing.bids.order_by('-amount').first()
        listings_with_bids.append({
            "listing": listing,
            "current_bid": current_bid
        })
    return render(request, "auctions/index.html", {
        "listings_with_bids": listings_with_bids
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


class ListingForm(forms.Form):
    title = forms.CharField(max_length=100)
    description = forms.CharField(widget=forms.Textarea)
    starting_bid = forms.DecimalField(decimal_places=2, max_digits=10)
    image_url = forms.URLField(required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)


@login_required
def create_listing(request):
    if request.method == "POST":
        form = ListingForm(request.POST)
        if form.is_valid():
            listing = Listing(
                title=form.cleaned_data["title"],
                description=form.cleaned_data["description"],
                starting_bid=form.cleaned_data["starting_bid"],
                image_url=form.cleaned_data["image_url"],
                category=form.cleaned_data["category"],
                owner=request.user
            )
            listing.save()
            return redirect("index")
    else:
        form = ListingForm()
    return render(request, "auctions/create_listing.html", {"form": form})


def listing(request, listing_id):
    listing = Listing.objects.get(pk=listing_id)
    current_bid = listing.bids.order_by('-amount').first()
    bid_form = BidForm()
    comment_form = CommentForm()

    if request.method == "POST":
        if "amount" in request.POST:
            bid_form = BidForm(request.POST)
            if bid_form.is_valid():
                amount = bid_form.cleaned_data["amount"]
                min_bid = listing.starting_bid
                if current_bid:
                    min_bid = max(min_bid, current_bid.amount + Decimal(0.01))
                if amount >= min_bid:
                    Bid.objects.create(user=request.user, listing=listing, amount=amount)
                    return redirect("listing", listing_id=listing.id)
                else:
                    bid_form.add_error("amount", f"Bid must be at least ${min_bid:.2f}")
        elif "content" in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                Comment.objects.create(
                    listing=listing,
                    author=request.user,
                    content=comment_form.cleaned_data["content"]
                )
                return redirect("listing", listing_id=listing.id)

    comments = listing.comments.order_by('-timestamp')
    return render(request, "auctions/listing.html", {
        "listing": listing,
        "current_bid": current_bid,
        "bid_form": bid_form,
        "comment_form": comment_form,
        "comments": comments
    })


class BidForm(forms.Form):
    amount = forms.DecimalField(decimal_places=2, max_digits=10, label="Your Bid")


class CommentForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), label="Add a comment")


@login_required
def add_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    listing.watchlist.add(request.user)
    return redirect("listing", listing_id=listing_id)


@login_required
def remove_watchlist(request, listing_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    listing.watchlist.remove(request.user)
    return redirect("listing", listing_id=listing_id)


@login_required
def watchlist(request):
    listings=request.user.watchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })