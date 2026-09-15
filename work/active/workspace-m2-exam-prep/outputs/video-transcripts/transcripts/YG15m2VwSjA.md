---
video_id: YG15m2VwSjA
url: https://www.youtube.com/watch?v=YG15m2VwSjA
title: Visualizing the chain rule and product rule | Chapter 4, Essence of calculus
channel: 3Blue1Brown
duration: 15:56
language: en
unit: L15
status: OK
---

[00:14] In the last videos I talked about the derivatives of simple functions,
[00:18] and the goal was to have a clear picture or intuition to hold in
[00:22] your mind that actually explains where these formulas come from.
[00:26] But most of the functions you deal with in modeling the world involve mixing,
[00:31] combining, or tweaking these simple functions in some other way,
[00:35] so our next step is to understand how you take derivatives of more complicated
[00:39] combinations.
[00:41] Again, I don't want these to be something to memorize,
[00:43] I want you to have a clear picture in mind for where each one comes from.
[00:49] Now, this really boils down into three basic ways to combine functions.
[00:54] You can add them together, you can multiply them,
[00:56] and you can throw one inside the other, known as composing them.
[01:00] Sure, you could say subtracting them, but really that's just
[01:03] multiplying the second by negative one and adding them together.
[01:08] Likewise, dividing functions doesn't really add anything,
[01:11] because that's the same as plugging one inside the function, one over x,
[01:14] and then multiplying the two together.
[01:17] So really, most functions you come across just involve layering
[01:20] together these three different types of combinations,
[01:23] though there's not really a bound on how monstrous things can become.
[01:27] But as long as you know how derivatives play with just those three combination types,
[01:31] you'll always be able to take it step by step and peel through
[01:34] the layers for any kind of monstrous expression.
[01:38] So the question is, if you know the derivative of two functions,
[01:42] what is the derivative of their sum, of their product,
[01:45] and of the function composition between them?
[01:50] The sum rule is easiest, if somewhat tongue-twisting to say out loud.
[01:54] The derivative of a sum of two functions is the sum of their derivatives.
[01:59] But it's worth warming up with this example by really thinking through
[02:03] what it means to take a derivative of a sum of two functions,
[02:07] since the derivative patterns for products and function composition won't
[02:11] be so straightforward, and they're going to require this kind of deeper thinking.
[02:16] For example, let's think about this function f of x equals sine of x plus x squared.
[02:22] It's a function where, for every input, you add together
[02:25] the values of sine of x and x squared at that point.
[02:29] For example, let's say at x equals 0.5, the height of the sine
[02:34] graph is given by this vertical bar, and the height of the x
[02:38] squared parabola is given by this slightly smaller vertical bar.
[02:44] And their sum is the length you get by just stacking them together.
[02:48] For the derivative, you want to ask what happens as you nudge that input slightly,
[02:53] maybe increasing it up to 0.5 plus dx.
[02:57] The difference in the value of f between those two places is what we call df.
[03:04] And when you picture it like this, I think you'll agree that the total
[03:08] change in the height is whatever the change to the sine graph is,
[03:13] what we might call d sine of x, plus whatever the change to x squared is, dx squared.
[03:22] We know that the derivative of sine is cosine, and remember what that means.
[03:27] It means that this little change, d sine of x, is about cosine of x times dx.
[03:33] It's proportional to the size of our initial nudge dx,
[03:37] and the proportionality constant equals cosine of whatever input we started at.
[03:43] Likewise, because the derivative of x squared is 2x,
[03:48] the change in the height of the x squared graph is 2x times whatever dx was.
[03:55] So rearranging df divided by dx, the ratio of the tiny change to
[04:00] the sum function to the tiny change in x that caused it,
[04:04] is indeed cosine of x plus 2x, the sum of the derivatives of its parts.
[04:11] But like I said, things are a bit different for products,
[04:15] and let's think through why in terms of tiny nudges again.
[04:20] In this case, I don't think graphs are our best bet for visualizing things.
[04:23] Pretty commonly in math, at a lot of levels of math really,
[04:27] if you're dealing with a product of two things,
[04:29] it helps to understand it as some kind of area.
[04:33] In this case, maybe you try to configure some mental setup
[04:36] of a box where the side lengths are sine of x and x squared.
[04:39] But what would that mean?
[04:42] Well, since these are functions, you might think of those sides as adjustable,
[04:46] dependent on the value of x, which maybe you think of as this
[04:49] number that you can just freely adjust up and down.
[04:53] So getting a feel for what this means, focus on
[04:56] that top side who changes as the function sine of x.
[05:01] As you change this value of x up from 0, it increases up to
[05:05] a length of 1 as sine of x moves up towards its peak,
[05:09] and after that it starts to decrease as sine of x comes down from 1.
[05:15] And in the same way, that height there is always changing as x squared.
[05:20] So f of x, defined as the product of these two functions, is the area of this box.
[05:27] And for the derivative, let's think about how
[05:30] a tiny change to x by dx influences that area.
[05:33] What is that resulting change in area df?
[05:39] Well, the nudge dx caused that width to change by some small d sine of x,
[05:44] and it caused that height to change by some dx squared.
[05:50] And this gives us three little snippets of new area,
[05:53] a thin rectangle on the bottom whose area is its width, sine of x,
[05:58] times its thin height, dx squared.
[06:01] And there's this thin rectangle on the right, whose area is its height,
[06:06] x squared, times its thin width, d sine of x.
[06:10] And there's also this little bit in the corner, but we can ignore that.
[06:14] Its area is ultimately proportional to dx squared,
[06:17] and as we've seen before, that becomes negligible as dx goes to zero.
[06:23] I mean, this whole setup is very similar to what I showed last video,
[06:27] with the x squared diagram.
[06:29] And just like then, keep in mind that I'm using somewhat beefy
[06:32] changes here to draw things, just so we can actually see them.
[06:36] But in principle, dx is something very very small,
[06:39] and that means that dx squared and d sine of x are also very very small.
[06:45] So, applying what we know about the derivative of sine and of x squared,
[06:51] that tiny change, dx squared, is going to be about 2x times dx.
[06:56] And that tiny change, d sine of x, well that's going to be about cosine of x times dx.
[07:02] As usual, we divide out by that dx to see that the ratio we want, df divided by dx,
[07:09] is sine of x times the derivative of x squared,
[07:12] plus x squared times the derivative of sine.
[07:17] And nothing we've done here is specific to sine or to x squared.
[07:21] This same line of reasoning would work for any two functions, g and h.
[07:27] And sometimes people like to remember this pattern with
[07:29] a certain mnemonic that you kind of sing in your head.
[07:32] Left d right, right d left.
[07:34] In this example, where we have sine of x times x squared, left d right,
[07:38] means you take that left function, sine of x, times the derivative of the right,
[07:43] in this case 2x.
[07:45] Then you add on right d left, that right function,
[07:48] x squared, times the derivative of the left one, cosine of x.
[07:54] Now out of context, presented as a rule to remember,
[07:57] I think this would feel pretty strange, don't you?
[08:00] But when you actually think of this adjustable box,
[08:03] you can see what each of those terms represents.
[08:06] Left d right is the area of that little bottom rectangle,
[08:10] and right d left is the area of that rectangle on the side.
[08:20] By the way, I should mention that if you multiply by a constant,
[08:23] say 2 times sine of x, things end up a lot simpler.
[08:27] The derivative is just the same as the constant multiplied by
[08:30] the derivative of the function, in this case 2 times cosine of x.
[08:35] I'll leave it to you to pause and ponder and verify that makes sense.
[08:41] Aside from addition and multiplication, the other common way to combine functions,
[08:46] and believe me, this one comes up all the time,
[08:49] is to shove one inside the other, function composition.
[08:53] For example, maybe we take the function x squared and shove it
[08:56] inside sine of x to get this new function, sine of x squared.
[09:01] What do you think the derivative of that new function is?
[09:05] To think this one through, I'll choose yet another way to visualize things,
[09:09] just to emphasize that in creative math, we've got lots of options.
[09:13] I'll put up three different number lines, the top one is going to hold the value of x,
[09:18] the second one is going to hold the x squared,
[09:21] and the third line is going to hold the value of sine of x squared.
[09:26] That is, the function x squared gets you from line 1 to line 2,
[09:30] and the function sine gets you from line 2 to line 3.
[09:34] As I shift around this value of x, maybe moving it up to the value 3,
[09:39] that second value stays pegged to whatever x squared is, in this case moving up to 9.
[09:46] That bottom value, being sine of x squared, is
[09:49] going to go to whatever sine of 9 happens to be.
[09:54] So, for the derivative, let's again start by nudging that x value by some little dx.
[10:01] I always think that it's helpful to think of x as starting
[10:04] at some actual concrete number, maybe 1.5 in this case.
[10:08] The resulting nudge to that second value, the change in x squared caused by such a dx,
[10:14] is dx squared.
[10:16] We could expand this like we have before, as 2x times dx,
[10:21] which for our specific input would be 2 times 1.5 times dx,
[10:25] but it helps to keep things written as dx squared, at least for now.
[10:31] In fact, I'm going to go one step further, give a new name to this x squared,
[10:36] maybe h, so instead of writing dx squared for this nudge, we write dh.
[10:42] This makes it easier to think about that third value, which is now pegged at sine of h.
[10:48] Its change is d sine of h, the tiny change caused by the nudge dh.
[10:55] By the way, the fact that it's moving to the left while the dh bump is going to the right
[11:00] just means that this change, d sine of h, is going to be some kind of negative number.
[11:06] Once again, we can use our knowledge of the derivative of the sine.
[11:10] This d sine of h is going to be about cosine of h times dh.
[11:15] That's what it means for the derivative of sine to be cosine.
[11:19] Unfolding things, we can replace that h with x squared again,
[11:23] so we know that the bottom nudge will be a size of cosine of x squared times dx squared.
[11:31] Let's unfold things even further.
[11:32] That intermediate nudge dx squared is going to be about 2x times dx.
[11:39] It's always a good habit to remind yourself of
[11:41] what an expression like this actually means.
[11:44] In this case, where we started at x equals 1.5 up top,
[11:48] this whole expression is telling us that the size of the nudge on that third
[11:54] line is going to be about cosine of 1.5 squared times 2 times 1.5 times whatever
[12:00] the size of dx was.
[12:02] It's proportional to the size of dx, and this
[12:05] derivative is giving us that proportionality constant.
[12:10] Notice what we came out with here.
[12:12] We have the derivative of the outside function,
[12:15] and it's still taking in the unaltered inside function,
[12:19] and then multiplying it by the derivative of that inside function.
[12:25] Again, there's nothing special about sine of x or x squared.
[12:29] If you have any two functions, g of x and h of x,
[12:33] the derivative of their composition, g of h of x,
[12:37] is going to be the derivative of g evaluated on h, multiplied by the derivative of h.
[12:47] This pattern right here is what we usually call the chain rule.
[12:52] Notice for the derivative of g, I'm writing it as dg dh instead of dg dx.
[12:58] On the symbolic level, this is a reminder that the thing you plug
[13:02] into that derivative is still going to be that intermediary function h.
[13:07] But more than that, it's an important reflection of what
[13:09] this derivative of the outer function actually represents.
[13:13] Remember, in our three line setup, when we took the derivative of the sine on
[13:18] that bottom, we expanded the size of that nudge, d sine, as cosine of h times dh.
[13:24] This was because we didn't immediately know how
[13:27] the size of that bottom nudge depended on x.
[13:30] That's kind of the whole thing we were trying to figure out.
[13:33] But we could take the derivative with respect to that intermediate variable, h.
[13:38] That is, figure out how to express the size of that nudge on the third
[13:41] line as some multiple of dh, the size of the nudge on the second line.
[13:46] It was only after that that we unfolded further by figuring out what dh was.
[13:53] In this chain rule expression, we're saying, look at the ratio between a tiny change in
[13:58] g, the final output, to a tiny change in h that caused it,
[14:02] h being the value we plug into g.
[14:05] Then multiply that by the tiny change in h, divided
[14:08] by the tiny change in x that caused it.
[14:12] So notice, those dh's cancel out, and they give us a ratio
[14:15] between the change in that final output and the change to the input that,
[14:19] through a certain chain of events, brought it about.
[14:23] And that cancellation of dh is not just a notational trick.
[14:26] That is a genuine reflection of what's going on with the
[14:30] tiny nudges that underpin everything we do with derivatives.
[14:36] So those are the three basic tools to have in your belt to handle
[14:39] derivatives of functions that combine a lot of smaller things.
[14:43] You've got the sum rule, the product rule, and the chain rule.
[14:48] And I'll be honest with you, there is a big difference between knowing
[14:51] what the chain rule is and what the product rule is,
[14:54] and actually being fluent with applying them in even the most hairy of situations.
[14:59] Watching videos, any videos, about the mechanics of calculus is
[15:03] never going to substitute for practicing those mechanics yourself,
[15:06] and building up the muscles to do these computations yourself.
[15:11] I really wish I could offer to do that for you,
[15:13] but I'm afraid the ball is in your court, my friend, to seek out the practice.
[15:18] What I can offer, and what I hope I have offered,
[15:20] is to show you where these rules actually come from.
[15:24] To show that they're not just something to be memorized and hammered away,
[15:27] but they're natural patterns, things that you too could have discovered
[15:31] just by patiently thinking through what a derivative actually means.
