# Best practices and tips for writing unit tests for Django applications

## How to improve your Django unit tests and make your applications more reliable


I think it’s never enough to repeat how valuable writing tests for your application is. When I was getting started in this field, I couldn’t see much value in writing tests. It felt like I was writing code that was invisible to the end-user and so what was the point of spending so much energy on this?

After many years, with multiple software projects under my belt, my point of view is the complete opposite. Writing tests is an absolutely essential part of writing good, reliable, and functional software.

Tests will make you a lot more confident about the code you‘re writing and will make things a lot smoother whenever you have to refactor some code you wrote a while back and don’t have everything 100% clear in your mind anymore. Also, whenever you need to upgrade your project’s dependencies, tests will let you rest assured that the upgrade didn’t break anything. Or, in the event that something actually broke, be able to cleanly fix the issue without frustrating any of your users.

One important thing though is that writing tests is not the end of it. Tests are still code that will evolve and need to be maintained across the lifetime of your application. With that in mind, in this article, we’ll look at some best practices and tips for writing good maintainable tests for your Django applications.

## 1. Make your tests concise

A common mistake when writing unit tests is making them very long by testing multiple things all at once. You should try to make your tests very precise by testing one thing at a time. This way, if a test breaks, you can quickly skim through the code and understand exactly what is being tested and why it broke.

Let’s say your writing tests for a password reset flow in your app. The user will type an email address and if there is an account registered with that email address, an email will be sent and the user will see a message telling them to check their inbox. If on the other hand there isn’t a user with that email address, you’d like to display a message to let them know that they probably signed up with a different address.

For testing the above, you could write a single test that checks for both situations:

```python
from django.test import TestCase

class MyAppTest(TestCase):

  def test_password_reset(self):
    # Simulates resetting password using a registered email address
    ...

    # Simulates resetting password using a non-registered email address
    ...
```


However, this makes your test harder to read as it will be longer and in the future if this test breaks, you will want to quickly glimpse at the code and know what it’s doing.

The best way to go about this is to write two separate tests grouped together in a dedicated test suite:

```python
from django.test import TestCase

class PasswordResetTest(TestCase):

  def test_password_reset_registered_email(self):
    ...

  def test_password_reset_non_registered_email(self):
    ...
```

So in practice, what you should do is write a `TestCase` subclass that groups together multiple tests and have each situation you’re testing be a separate method in that class. Also, make sure to only group together tests that make sense together. Adding a lot of test methods to the same class when the tests are unrelated will make your tests less readable.

One thing to always remember is that **you will spend most of your time reading code** not writing it, so readability is super important.

## 2. Document your tests

You will usually write tests at the same time you’re coding the feature that’s being tested (or maybe immediately after you’re done implementing it). At that time, things will be fresh in your mind and you may feel like documenting your tests is unnecessary.

But remember, the goal of writing tests is to make sure a feature you wrote a while ago keeps working as you continue to improve and work on your application. That means that your tests will likely break when you’re working on something that you thought was completely unrelated to that initial test. And that time, you’ll have no idea what that test is about.

So to stay at peace with your future self, make sure to always write a clear docstring for your tests, explaining what the test is for and the results that are expected from the test.

```python
from django.test import TestCase

class PasswordResetTest(TestCase):

  def test_password_reset_registered_email(self):
    '''Simulates a user trying to reset their password submitting an email
    address that belongs to a registered user.

    An email should be sent to the user and a message should be displayed
    letting them know.'''
    ...

  def test_password_reset_non_registered_email(self):
    '''Simulates a user trying to reset their password submitting an email
    address that doesn't belong to a registered user.

    No emails should be sent and only an error message should be displayed.'''
    ...
```

Trust me, your future self will thank you.

Your future self finding a well-documented unit test that needs maintenance

## 3. Mock only what’s necessary

When writing tests, it’s common practice to mock out calls to external services that your application depends on. If your application depends on some SDK that calls an external API, you wouldn’t want to call that API every time you run your tests. For that, you use [mocks](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.MagicMock).

You should keep in mind though that you should only mock the code that you don’t own. If you have a wrapper class that encapsulates calls to some external API, do not mock your class, but the external calls themselves.

Let’s say you have some service class in your app that fetches the latest price of some cryptocurrency:

```python
import requests

class CryptoServiceError(Exception):
  pass

class CryptoService:

  def get_latest_price(self, ticker: str) -> float:
    response = request.get(f"https://api2.binance.com/api/v3/ticker/price?symbol={ticker}")
    if response.status_code != 200:
      raise CryptoServiceError(f"Failed connecting to Binance API. Status code: {response.status_code}")

    data = response.json()
    return float(data["price"])

```

If you were to write a unit test of some part of your code that uses this class, you should not just mock the calls to `get_latest_price` and call it a day. The way you handle the data that is returned by the API may contain bugs and so that should be tested too.

Ideally, you should write a test suite for this service class containing multiple tests that will each simulate a different response from the external service. This way you can be sure that you’re dealing with all possible outcomes.

As for the classes that depend on this `CryptoService` class, you’re fine mocking it out for those tests. But that’s as long as you have a dedicated test suite to the service class itself.

## 4. Be careful with dates

Your tests should be reliable enough that they won’t be breaking for silly reasons. So when writing tests for components and parts of your code that depend on dates, there’s one thing you should be careful about.

Let’s say you have a component in your app that deals with generating reports that depend on a range of dates. For your test, you need a date that is one hour less than the current time **but still on the same day**.

If you simply subtract one hour from the time when the test is being run, your test will break depending on the time of day that it’s run. Moreover, if you have people working on the same project across different time zones, the behavior will differ depending on their time zones.

For that reason, whenever you’re working with dates in your tests, it’s always best to hard-code them and never simply use the current time (such as by calling the `now()` function in the `django.utils.timezone` package).

```python
from django.tests import TestCase
from django.utils import timezone
import datetime as dt

class MyAppTest(TestCase):

  def test_report_generation(self):

    # This is bad
    start_date = timezone.now()

    # This is good
    start_date = dt.datetime(year=2022, month=2, day=23, hour=15, minute=23)
```

Hard-code dates in your tests and stay free from [heisenbugs](https://en.wikipedia.org/wiki/Heisenbug)

This way your tests will always behave the same, no matter when they are running.

## 5. Check your test coverage

To make sure that your tests are going through every dark corner of your code, you need to check their coverage.

For python tests, you can use the great [coverage.py](https://coverage.readthedocs.io/) library. This library will check all lines of code that are being executed when you run your tests and generate an HTML report in the end.

Having 100% of test coverage is not a guarantee that your software is bug-free but it surely helps!

## Conclusion

If you’re serious about writing great software, then writing tests should be part of your routine.

I hope you enjoyed this tutorial! Hit me up if you have any questions.
