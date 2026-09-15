---
video_id: 8JIe_cz6qGA
url: https://www.youtube.com/watch?v=8JIe_cz6qGA
title: Hypothesis testing (ALL YOU NEED TO KNOW!)
channel: zedstatistics
duration: 68:16
language: en
unit: L10
status: OK
---

[00:00] hey gang welcome to the third video on statistical inference this one being on
[00:05] statistical inference this one being on hypothesis testing my name's Justin
[00:08] hypothesis testing my name's Justin zeltser and I'll put all the videos in
[00:10] zeltser and I'll put all the videos in the series up on Z statistics com or if
[00:15] the series up on Z statistics com or if you're watching via University you'll be
[00:17] you're watching via University you'll be able to see them in each of the module
[00:19] able to see them in each of the module pages so this will be module 3 now this
[00:24] pages so this will be module 3 now this is quite an extensive look at hypothesis
[00:26] is quite an extensive look at hypothesis testing so if you're new to it see if
[00:30] testing so if you're new to it see if you can get through the video because it
[00:32] you can get through the video because it really is quite a complete picture of
[00:35] really is quite a complete picture of hypothesis testing and I'm gonna start
[00:38] hypothesis testing and I'm gonna start with a bit of a look into the intuition
[00:40] with a bit of a look into the intuition behind hypothesis testing it won't
[00:44] behind hypothesis testing it won't involve any numbers but I think it's
[00:46] involve any numbers but I think it's quite a good way to start to get us get
[00:48] quite a good way to start to get us get our minds in the right frame for it
[00:51] our minds in the right frame for it we're then going to look at an example
[00:53] we're then going to look at an example and that's going to lead us through the
[00:55] and that's going to lead us through the rest of the video so we'll use that
[00:57] rest of the video so we'll use that example we'll use that example in
[00:59] example we'll use that example in looking at all the other subtopics and
[01:03] looking at all the other subtopics and after we get familiar with this example
[01:06] after we get familiar with this example we're going to look at these first three
[01:08] we're going to look at these first three sub topics which are all somewhat
[01:11] sub topics which are all somewhat related the first one is about the null
[01:13] related the first one is about the null hypothesis would be defining what that
[01:16] hypothesis would be defining what that is looking at the alternate hypothesis
[01:19] is looking at the alternate hypothesis as well we'll be dealing with this
[01:21] as well we'll be dealing with this concept of level of significance which
[01:23] concept of level of significance which is a very important concept
[01:25] is a very important concept we'll then look at this idea of a test
[01:29] we'll then look at this idea of a test statistic so in any given hypothesis
[01:31] statistic so in any given hypothesis test you generate one of these and in
[01:35] test you generate one of these and in doing so you can also generate an
[01:36] doing so you can also generate an accompanying p-value the much-maligned
[01:40] accompanying p-value the much-maligned p-value and statistical circles at least
[01:42] p-value and statistical circles at least we'll be looking at all three of these
[01:44] we'll be looking at all three of these concepts which as I said are all related
[01:48] concepts which as I said are all related and what I mean by that is that they
[01:51] and what I mean by that is that they have the same perspective which is the
[01:54] have the same perspective which is the null hypothesis we'll see what that
[01:56] null hypothesis we'll see what that means when we get there but they all
[01:58] means when we get there but they all essentially assume the null hypothesis
[02:00] essentially assume the null hypothesis is true anyway after that we'll go on to
[02:04] is true anyway after that we'll go on to discussing what a confidence interval is
[02:07] discussing what a confidence interval is all about we've kind of loosely touched
[02:10] all about we've kind of loosely touched on this in previous videos in the series
[02:13] on this in previous videos in the series but the reason why I'm bringing up
[02:15] but the reason why I'm bringing up bringing it up again here is that it's
[02:18] bringing it up again here is that it's kind of like an equal and opposite
[02:20] kind of like an equal and opposite measure of the p-value they actually
[02:22] measure of the p-value they actually work in tandem but the difference being
[02:25] work in tandem but the difference being confidence intervals have the
[02:26] confidence intervals have the perspective of the sample whereas your
[02:28] perspective of the sample whereas your p-value has the perspective of your null
[02:31] p-value has the perspective of your null hypothesis so look if these terms don't
[02:34] hypothesis so look if these terms don't mean anything to you just hold on two
[02:36] mean anything to you just hold on two seconds and we'll get into it you
[02:39] seconds and we'll get into it you noticed but if you've been to your
[02:42] noticed but if you've been to your lectures and you've sort of heard these
[02:43] lectures and you've sort of heard these terms thrown around I'm just giving you
[02:46] terms thrown around I'm just giving you a bit of a picture as to where we're
[02:47] a bit of a picture as to where we're going to be dealing with them we're then
[02:51] going to be dealing with them we're then going to look at significant treatment
[02:52] going to look at significant treatment difference power and sample size as well
[02:55] difference power and sample size as well and this is actually my favorite bit so
[02:58] and this is actually my favorite bit so if you can stick around to the power and
[03:00] if you can stick around to the power and sample size section I think if I can say
[03:04] sample size section I think if I can say so I do a pretty good job of trying to
[03:06] so I do a pretty good job of trying to get an intuitive look at power and
[03:09] get an intuitive look at power and sample size as well so with all that
[03:12] sample size as well so with all that done we'll finally have a look at a
[03:15] done we'll finally have a look at a final we'll finally have a look at an
[03:17] final we'll finally have a look at an example here a different one
[03:19] example here a different one and it'll give you a chance to put what
[03:22] and it'll give you a chance to put what you have learned into practice and
[03:25] you have learned into practice and there's quite a lot of algebra here as
[03:27] there's quite a lot of algebra here as well so there's a lot to get through but
[03:31] well so there's a lot to get through but it should be a fun little journey and
[03:33] it should be a fun little journey and hopefully by the end you're going to be
[03:35] hopefully by the end you're going to be tip-top around your hypothesis tests so
[03:41] tip-top around your hypothesis tests so let us begin with the intuition behind
[03:43] let us begin with the intuition behind hypothesis testing so say that you think
[03:48] hypothesis testing so say that you think one dollar coins are tail biased and
[03:53] one dollar coins are tail biased and what I mean by that is that maybe they
[03:55] what I mean by that is that maybe they flip more tails than they do heads for
[03:58] flip more tails than they do heads for whatever reason maybe there's subtle
[04:00] whatever reason maybe there's subtle emore coin on the head side of the coin
[04:03] emore coin on the head side of the coin so it weighs it down or something like
[04:05] so it weighs it down or something like that
[04:05] that I don't know it's a silly example but at
[04:08] I don't know it's a silly example but at least it gives us something we can
[04:10] least it gives us something we can visualize the question is how you would
[04:12] visualize the question is how you would test this hypothesis scientifically now
[04:19] test this hypothesis scientifically now you might tell me that firstly you got
[04:21] you might tell me that firstly you got to flip a bunch of coins
[04:22] to flip a bunch of coins obviously you got to take some kind of
[04:24] obviously you got to take some kind of sample or do an experiment
[04:26] sample or do an experiment that's true you then have to get out a
[04:29] that's true you then have to get out a pen and paper and note the proportion of
[04:31] pen and paper and note the proportion of tails you have in your sample but then
[04:36] tails you have in your sample but then what what happens then how do you know
[04:39] what what happens then how do you know whether yes this coin is now biased or
[04:41] whether yes this coin is now biased or no this coin is not biased well that's
[04:45] no this coin is not biased well that's where hypothesis testing is going to
[04:47] where hypothesis testing is going to come in and help you out it's going to
[04:49] come in and help you out it's going to help you solve this riddle of yours that
[04:53] help you solve this riddle of yours that you've constructed for yourself and I've
[04:56] you've constructed for yourself and I've put together a visualization to help us
[04:59] put together a visualization to help us out here
[05:00] out here this is the number of tails from 100
[05:03] this is the number of tails from 100 tosses of a fair coin now the important
[05:07] tosses of a fair coin now the important portent part of this sentence is the
[05:09] portent part of this sentence is the word fair there so if the coin was fair
[05:13] word fair there so if the coin was fair as in not biased you might expect this
[05:16] as in not biased you might expect this being the probability distribution of
[05:20] being the probability distribution of possible outcomes from that 100 tosses
[05:23] possible outcomes from that 100 tosses of the coin it's not as if you have to
[05:25] of the coin it's not as if you have to get 50 tails from your 100 tosses of the
[05:28] get 50 tails from your 100 tosses of the coin right you might get 51 or 52 or
[05:31] coin right you might get 51 or 52 or it's even possible to get say 60 or 61
[05:34] it's even possible to get say 60 or 61 tails out of a hundred and it still come
[05:38] tails out of a hundred and it still come from a fair coin it just so happened you
[05:40] from a fair coin it just so happened you had a very random sample very extreme
[05:43] had a very random sample very extreme sample now before we interrogate this
[05:46] sample now before we interrogate this further I'm gonna change this from the
[05:48] further I'm gonna change this from the number of tails from 100 tosses to the
[05:51] number of tails from 100 tosses to the proportion of tails from 100 tosses of a
[05:55] proportion of tails from 100 tosses of a fair coin nothing else changes 50 now
[05:57] fair coin nothing else changes 50 now becomes 0.5 but this just allows us to
[06:01] becomes 0.5 but this just allows us to generalize beyond this particular number
[06:04] generalize beyond this particular number of tosses of a coin so yes looking at
[06:08] of tosses of a coin so yes looking at this distribution you might notice that
[06:09] this distribution you might notice that it's centered around 0.5 and that indeed
[06:14] it's centered around 0.5 and that indeed is what we might expect to get from our
[06:16] is what we might expect to get from our sample that's our expectation but say we
[06:19] sample that's our expectation but say we had a sample that we got 52 tails in is
[06:24] had a sample that we got 52 tails in is that necessarily evidence of bias in
[06:27] that necessarily evidence of bias in this coin well no it seems quite
[06:29] this coin well no it seems quite reasonable that from a fair coin we
[06:32] reasonable that from a fair coin we could have just got 52 tails out of 100
[06:36] could have just got 52 tails out of 100 but what then if we get a sample of 62
[06:39] but what then if we get a sample of 62 tails
[06:41] tails does that cast any doubt on the idea
[06:45] does that cast any doubt on the idea that the true proportion that the true
[06:48] that the true proportion that the true probability is 0.5 well if you can see
[06:52] probability is 0.5 well if you can see that this sample outcome casts more
[06:55] that this sample outcome casts more doubt on the coins fairness then this
[06:59] doubt on the coins fairness then this sample outcome you've effectively got
[07:02] sample outcome you've effectively got the right mind state for hypothesis
[07:04] the right mind state for hypothesis testing and that's in fact all we're
[07:06] testing and that's in fact all we're doing we're assessing our sample for how
[07:09] doing we're assessing our sample for how extreme it is that's all hypothesis test
[07:12] extreme it is that's all hypothesis test is it looks at a sample and asks how
[07:14] is it looks at a sample and asks how extreme is that sample and what will
[07:17] extreme is that sample and what will happen is we'll create this barrier or
[07:20] happen is we'll create this barrier or critical value beyond which we're happy
[07:23] critical value beyond which we're happy to say yeah it's now becoming too
[07:25] to say yeah it's now becoming too extreme for us to really maintain this
[07:28] extreme for us to really maintain this coins fairness but if they'll sample
[07:32] coins fairness but if they'll sample lies on the left side of this so say we
[07:35] lies on the left side of this so say we got this 52 tails outcome we might say
[07:37] got this 52 tails outcome we might say yeah look it's greater than 50 but it's
[07:41] yeah look it's greater than 50 but it's not extreme enough it's well within the
[07:43] not extreme enough it's well within the realms of possibilities from a fair coin
[07:47] realms of possibilities from a fair coin that my friends is a hypothesis test
[07:51] that my friends is a hypothesis test where your null hypothesis you're sort
[07:54] where your null hypothesis you're sort of starting value might be that theta
[07:56] of starting value might be that theta the true proportion of coins is 0.5 that
[07:59] the true proportion of coins is 0.5 that it's that black line there and we're
[08:02] it's that black line there and we're gonna see if we have enough evidence
[08:03] gonna see if we have enough evidence we're gonna see if our sample is use
[08:06] we're gonna see if our sample is use extreme enough to suggest that the true
[08:10] extreme enough to suggest that the true proportions of greater than 0.5 in other
[08:13] proportions of greater than 0.5 in other words this coin is biased so we're gonna
[08:17] words this coin is biased so we're gonna use this sample of a hundred coin tosses
[08:20] use this sample of a hundred coin tosses to make an inference about the true
[08:24] to make an inference about the true population probability theta now as I
[08:29] population probability theta now as I said this value here might be our
[08:31] said this value here might be our critical value and beyond this point
[08:33] critical value and beyond this point we're going to start saying yep that is
[08:35] we're going to start saying yep that is now too extreme for us to realistically
[08:37] now too extreme for us to realistically hold on to this null hypothesis of theta
[08:40] hold on to this null hypothesis of theta being point 5 and that's actually called
[08:43] being point 5 and that's actually called the rejection region that's the region
[08:45] the rejection region that's the region in which we will be comfortable
[08:47] in which we will be comfortable rejecting our null hypothesis now if
[08:51] rejecting our null hypothesis now if you're a bit of a smartypants or you've
[08:52] you're a bit of a smartypants or you've paid attention in your lecture
[08:54] paid attention in your lecture you might realize that there's two
[08:56] you might realize that there's two possible ways of looking at our
[08:58] possible ways of looking at our alternate hypothesis you know you might
[09:01] alternate hypothesis you know you might note we have a one-tailed alternate
[09:02] note we have a one-tailed alternate hypothesis here so we're only going to
[09:05] hypothesis here so we're only going to be rejecting this null hypothesis in one
[09:07] be rejecting this null hypothesis in one direction so in other words if our tails
[09:10] direction so in other words if our tails vastly exceeds our heads but it's also
[09:15] vastly exceeds our heads but it's also possible to do a two-tailed test as well
[09:17] possible to do a two-tailed test as well and the difference might be instead of
[09:20] and the difference might be instead of having a strict one-sided inequality in
[09:23] having a strict one-sided inequality in the alternate hypothesis this one it
[09:25] the alternate hypothesis this one it actually goes both ways so we'll have
[09:27] actually goes both ways so we'll have two different critical values what this
[09:30] two different critical values what this means is that if we have a sample that
[09:34] means is that if we have a sample that is extreme in either direction we're
[09:36] is extreme in either direction we're happy to reject our null hypothesis so
[09:39] happy to reject our null hypothesis so it really depends on what kind of
[09:41] it really depends on what kind of question you're asking are you asking
[09:42] question you're asking are you asking specifically about the coin being tail
[09:45] specifically about the coin being tail biased as in more tales than heads or
[09:49] biased as in more tales than heads or are you asking whether the coin is just
[09:50] are you asking whether the coin is just biased in general and if it's the latter
[09:54] biased in general and if it's the latter we might have two rejection regions one
[09:57] we might have two rejection regions one on the extreme positive side and one on
[09:59] on the extreme positive side and one on the extreme negative side but again all
[10:03] the extreme negative side but again all we're doing is looking at the sample
[10:04] we're doing is looking at the sample value and saying how extreme is it is it
[10:07] value and saying how extreme is it is it too extreme for us to maintain this null
[10:11] too extreme for us to maintain this null hypothesis okay so I feel like I've
[10:17] hypothesis okay so I feel like I've massaged your skulls into the right so
[10:20] massaged your skulls into the right so that they are now perfect absorbency for
[10:23] that they are now perfect absorbency for the actual nuts and bolts of all this so
[10:25] the actual nuts and bolts of all this so let's have a look at the example I
[10:27] let's have a look at the example I provided here and these two examples I
[10:30] provided here and these two examples I give on this particular lecture here are
[10:33] give on this particular lecture here are both to do with the same surgical
[10:36] both to do with the same surgical concern which is to operate or not to
[10:39] concern which is to operate or not to operate its first example deals with
[10:43] operate its first example deals with proximal humerus fractures in the
[10:45] proximal humerus fractures in the elderly and say something in the
[10:48] elderly and say something in the shoulder I'm told can you tell I'm a
[10:51] shoulder I'm told can you tell I'm a statistician and not someone medically
[10:53] statistician and not someone medically trained nonetheless we can do the stats
[10:56] trained nonetheless we can do the stats on this we have two particular treatment
[10:58] on this we have two particular treatment options here we have an operative
[11:00] options here we have an operative treatment and we also have physio only
[11:06] treatment and we also have physio only so for the operative patients or the
[11:08] so for the operative patients or the patients that were treated operatively
[11:11] patients that were treated operatively 62 had positive outcomes out of a
[11:14] 62 had positive outcomes out of a hundred after six months whereas those
[11:17] hundred after six months whereas those that were given physio only had 48 out
[11:20] that were given physio only had 48 out of a hundred with an improved outcome
[11:23] of a hundred with an improved outcome after six months so this is a very
[11:25] after six months so this is a very simplified example obviously with nice
[11:27] simplified example obviously with nice round numbers so we don't have to get to
[11:30] round numbers so we don't have to get to numerically intense the question is can
[11:35] numerically intense the question is can we conduct a full hypothesis test to
[11:36] we conduct a full hypothesis test to answer the following questions is there
[11:39] answer the following questions is there evidence of a difference in outcomes
[11:41] evidence of a difference in outcomes between the two treatments and B say the
[11:46] between the two treatments and B say the orthopedic Society requires an outcome
[11:49] orthopedic Society requires an outcome improvement of at least 5 percent before
[11:51] improvement of at least 5 percent before updating treatment protocols should they
[11:55] updating treatment protocols should they recommend surgery for proximal humerus
[11:57] recommend surgery for proximal humerus fractures so here the idea is that it's
[12:01] fractures so here the idea is that it's not just good enough that operative
[12:04] not just good enough that operative treatment is slightly better than physio
[12:06] treatment is slightly better than physio they need it to be at least a 5 percent
[12:09] they need it to be at least a 5 percent better than physio to start recommending
[12:12] better than physio to start recommending surgery so let's maybe there's an
[12:14] surgery so let's maybe there's an additional there might be additional
[12:17] additional there might be additional risks to the patient when they go under
[12:20] risks to the patient when they go under the knife so those additional risks need
[12:22] the knife so those additional risks need to be offset by this additional buffer
[12:24] to be offset by this additional buffer here anyway feel free to actually if you
[12:29] here anyway feel free to actually if you think you're confident you know how to
[12:30] think you're confident you know how to do these sorts of questions by all means
[12:33] do these sorts of questions by all means stop the video here and have a go and
[12:35] stop the video here and have a go and see if you can come up with an answer
[12:39] see if you can come up with an answer but I will hint at this being a
[12:41] but I will hint at this being a two-tailed test so you can see we've
[12:44] two-tailed test so you can see we've asked is there evidence of a difference
[12:45] asked is there evidence of a difference in outcome so it doesn't matter which
[12:47] in outcome so it doesn't matter which way it goes now hypothesis test here
[12:53] way it goes now hypothesis test here will be two-tailed all right
[12:56] will be two-tailed all right let's tuck in let's talk about null
[12:58] let's tuck in let's talk about null hypothesis so finally we actually get to
[13:00] hypothesis so finally we actually get to deal with some of the theory here let's
[13:03] deal with some of the theory here let's call for the to start with p1 the
[13:05] call for the to start with p1 the probability of a positive outcome for
[13:07] probability of a positive outcome for the operative group and P naught is the
[13:09] the operative group and P naught is the probability of a positive outcome for
[13:11] probability of a positive outcome for the non operative group the physio only
[13:14] the non operative group the physio only group
[13:16] so our null hypothesis here is theta
[13:19] so our null hypothesis here is theta which is the population parameter for
[13:21] which is the population parameter for the difference between these two
[13:24] the difference between these two probabilities we're gonna say set that
[13:28] probabilities we're gonna say set that equal to zero in our null hypothesis and
[13:31] equal to zero in our null hypothesis and our alternate hypothesis is that theta
[13:34] our alternate hypothesis is that theta is not equal to zero
[13:37] is not equal to zero now in general the way of thinking about
[13:39] now in general the way of thinking about a hypothesis test or at least the
[13:42] a hypothesis test or at least the attitude towards hypothesis tests from
[13:44] attitude towards hypothesis tests from statisticians is that we're always very
[13:47] statisticians is that we're always very pessimistic so for example say we're
[13:50] pessimistic so for example say we're trying to show that there's a difference
[13:51] trying to show that there's a difference between these two groups the first thing
[13:56] between these two groups the first thing we do is we assume that there's no
[13:59] we do is we assume that there's no difference so we assume that there's no
[14:02] difference so we assume that there's no difference and see if there's enough
[14:03] difference and see if there's enough evidence to infer that there is a
[14:05] evidence to infer that there is a difference we don't simply assume the
[14:08] difference we don't simply assume the thing is true that we're trying to show
[14:10] thing is true that we're trying to show first and then try to disprove it no
[14:14] first and then try to disprove it no we're pessimistic we always assume the
[14:16] we're pessimistic we always assume the reverse is true so if we're trying to
[14:18] reverse is true so if we're trying to seek evidence for a difference we'll
[14:22] seek evidence for a difference we'll first assume that there's no difference
[14:24] first assume that there's no difference and then in our alternative hypothesis
[14:27] and then in our alternative hypothesis we'll have finally that there is a
[14:29] we'll have finally that there is a difference between these two groups so
[14:32] difference between these two groups so another way of saying that is that
[14:34] another way of saying that is that whatever you're seeking evidence for
[14:36] whatever you're seeking evidence for this is a really good line whatever
[14:38] this is a really good line whatever you're seeking evidence for goes in your
[14:41] you're seeking evidence for goes in your alternate hypothesis we are seeking
[14:44] alternate hypothesis we are seeking evidence to show that there's a
[14:46] evidence to show that there's a difference between the two groups so
[14:49] difference between the two groups so that goes in our alternate hypothesis
[14:51] that goes in our alternate hypothesis and I can almost see the question now
[14:54] and I can almost see the question now getting typed in the comments section
[14:56] getting typed in the comments section which is can you seek evidence to show
[14:59] which is can you seek evidence to show that the difference is zero can you seek
[15:02] that the difference is zero can you seek evidence for sameness my answer is well
[15:06] evidence for sameness my answer is well no not really
[15:09] no not really certainly not in very simple forms of
[15:11] certainly not in very simple forms of statistics so our null hypothesis will
[15:14] statistics so our null hypothesis will always be some kind of equality and our
[15:17] always be some kind of equality and our alternate hypothesis is that in equality
[15:20] alternate hypothesis is that in equality seeking that difference
[15:24] now the question is if the null hypothesis is true
[15:27] hypothesis is true how will the sampling statistic now for
[15:31] how will the sampling statistic now for the moment let's just say the sampling
[15:32] the moment let's just say the sampling statistic is sort of theta with a hat on
[15:34] statistic is sort of theta with a hat on it what we can get from our sample which
[15:37] it what we can get from our sample which will be our samples p1 minus our samples
[15:40] will be our samples p1 minus our samples P naught now if the null hypothesis is
[15:43] P naught now if the null hypothesis is true how will it be distributed well
[15:46] true how will it be distributed well much like our slide on the intuition
[15:50] much like our slide on the intuition behind hypothesis testing
[15:52] behind hypothesis testing it'll be distributed like a nice
[15:54] it'll be distributed like a nice bell-shaped curve so again the important
[15:58] bell-shaped curve so again the important part of this is that the null hypothesis
[15:59] part of this is that the null hypothesis here is assumed to be true so if indeed
[16:03] here is assumed to be true so if indeed there is no difference in the population
[16:05] there is no difference in the population between the two groups our sample should
[16:09] between the two groups our sample should expect no difference between the two
[16:12] expect no difference between the two sample values and when I say expect I
[16:14] sample values and when I say expect I mean that that's the middle of the
[16:15] mean that that's the middle of the distribution due to random variation of
[16:18] distribution due to random variation of course there will be some kind of
[16:20] course there will be some kind of probability distribution around that
[16:21] probability distribution around that some kind of variance around this sample
[16:24] some kind of variance around this sample value of zero
[16:27] but what variants how can you describe
[16:31] but what variants how can you describe this distribution well the expected
[16:34] this distribution well the expected value of this distribution as I just
[16:35] value of this distribution as I just said is zero it's the middle of this
[16:37] said is zero it's the middle of this plot which makes sense because if the
[16:40] plot which makes sense because if the null hypothesis is true if you sampled a
[16:43] null hypothesis is true if you sampled a hundred patients that have the operative
[16:45] hundred patients that have the operative treatment and 100 patients that have
[16:47] treatment and 100 patients that have physio only you would expect them to
[16:50] physio only you would expect them to have the same proportion of successful
[16:53] have the same proportion of successful outcomes that should be the middle of
[16:54] outcomes that should be the middle of the distribution but what is the
[16:56] the distribution but what is the variance of this distribution well
[16:58] variance of this distribution well you'll note that we actually have two
[17:00] you'll note that we actually have two random variables here P 1 and P naught
[17:03] random variables here P 1 and P naught and this just involves a little bit of
[17:05] and this just involves a little bit of your recollection of linear algebra the
[17:08] your recollection of linear algebra the variance of two uncorrelated random
[17:12] variance of two uncorrelated random variables is just the variance of 1 plus
[17:15] variables is just the variance of 1 plus the variance of the other so the
[17:17] the variance of the other so the variance of a proportion is in fact that
[17:20] variance of a proportion is in fact that proportion times 1 minus the proportion
[17:22] proportion times 1 minus the proportion divided by the number of observations
[17:25] divided by the number of observations and the same will be true for the physio
[17:28] and the same will be true for the physio only group now if you recall when we
[17:30] only group now if you recall when we were looking at the contents of the
[17:32] were looking at the contents of the whole video I noted that
[17:35] whole video I noted that this particular subtopic among three
[17:38] this particular subtopic among three subtopics takes the perspective of the
[17:40] subtopics takes the perspective of the null hypothesis we're assuming the null
[17:43] null hypothesis we're assuming the null hypothesis is true so that means that P
[17:46] hypothesis is true so that means that P one and P naught are actually going to
[17:48] one and P naught are actually going to be the same so what we can do here is
[17:51] be the same so what we can do here is that this distribution here assumes the
[17:53] that this distribution here assumes the null hypothesis is true so that I can
[17:55] null hypothesis is true so that I can change this P 1 and P naught into just P
[17:58] change this P 1 and P naught into just P which is this sort of grouped mean or
[18:01] which is this sort of grouped mean or grouped proportion so they're actually
[18:03] grouped proportion so they're actually the same here and so we can simplify
[18:05] the same here and so we can simplify this a little bit to be P times 1 minus
[18:07] this a little bit to be P times 1 minus P times 1 on N 1 plus 1 on n naught so
[18:13] P times 1 on N 1 plus 1 on n naught so feeder hat here we go is distributed
[18:16] feeder hat here we go is distributed normally with a mean of 0 and a variance
[18:18] normally with a mean of 0 and a variance given by this now again I see a question
[18:22] given by this now again I see a question someone I'm sure is going to be asking
[18:25] someone I'm sure is going to be asking me why on earth is this distributed
[18:27] me why on earth is this distributed normally we have a difference between
[18:29] normally we have a difference between two proportions these are essentially
[18:33] two proportions these are essentially binomial distributions why is this
[18:36] binomial distributions why is this normal and this is the lovely thing
[18:38] normal and this is the lovely thing about statistics as soon as you sample
[18:40] about statistics as soon as you sample enough as soon as your sample size is
[18:43] enough as soon as your sample size is big enough everything just becomes
[18:44] big enough everything just becomes normal I feel like every statistician
[18:47] normal I feel like every statistician should have a CLT tattoo on them
[18:50] should have a CLT tattoo on them somewhere without it we would be much
[18:53] somewhere without it we would be much worse off CLT standing for the central
[18:56] worse off CLT standing for the central limit theorem which allows us to put
[18:58] limit theorem which allows us to put this B in here and say that in large
[19:00] this B in here and say that in large samples sampling statistics tend to
[19:04] samples sampling statistics tend to become normally distributed all right so
[19:11] become normally distributed all right so let's go in a little bit further what's
[19:13] let's go in a little bit further what's going to happen here is that we're going
[19:14] going to happen here is that we're going to construct well there'll be two
[19:17] to construct well there'll be two separate rejection regions each of which
[19:20] separate rejection regions each of which will have well there'll be two separate
[19:23] will have well there'll be two separate rejection regions which in combination
[19:26] rejection regions which in combination will sum up to 0.05 now why does it sum
[19:30] will sum up to 0.05 now why does it sum up to 0.05 well that's just our choice
[19:32] up to 0.05 well that's just our choice we're gonna label this thing called
[19:35] we're gonna label this thing called alpha as 0.05 and all that means is that
[19:38] alpha as 0.05 and all that means is that this is the probability that we're
[19:42] this is the probability that we're willing to accept we're willing to take
[19:44] willing to accept we're willing to take on board in rejecting a null hypothesis
[19:48] on board in rejecting a null hypothesis that might be
[19:48] that might be true right let's just rewind that a
[19:52] true right let's just rewind that a little bit if we get a sample in this
[19:56] little bit if we get a sample in this yellow region here we're going to be
[19:59] yellow region here we're going to be rejecting the null hypothesis that's how
[20:01] rejecting the null hypothesis that's how we've constructed this hypothesis test
[20:03] we've constructed this hypothesis test but realize that this distribution goes
[20:06] but realize that this distribution goes on for infinity so this black line the
[20:09] on for infinity so this black line the distribution which is the probability
[20:11] distribution which is the probability density function function where the null
[20:14] density function function where the null hypothesis is true it goes on for
[20:16] hypothesis is true it goes on for infinity so it's still possible if our
[20:19] infinity so it's still possible if our sample difference is 0.15 or 0.2 it's
[20:22] sample difference is 0.15 or 0.2 it's still possible for this null hypothesis
[20:25] still possible for this null hypothesis to be true yet our sample just be very
[20:27] to be true yet our sample just be very extreme so essentially we create
[20:31] extreme so essentially we create artificially mind you this region beyond
[20:35] artificially mind you this region beyond which we're sure enough and so this
[20:39] which we're sure enough and so this yellow area represents the chance we're
[20:42] yellow area represents the chance we're willing to take on board that were
[20:43] willing to take on board that were actually going to be incorrectly
[20:45] actually going to be incorrectly rejecting a true null hypothesis
[20:48] rejecting a true null hypothesis now why 0.05 well they won't tell you
[20:53] now why 0.05 well they won't tell you this in your lecture but there's no
[20:55] this in your lecture but there's no reason at all
[20:57] reason at all statisticians love 0.05 and of course
[21:00] statisticians love 0.05 and of course it's a we're attracted to it because
[21:02] it's a we're attracted to it because it's nice and round but it's completely
[21:06] it's nice and round but it's completely arbitrary someone chose 0.05 many years
[21:11] arbitrary someone chose 0.05 many years ago someone probably by the name of
[21:12] ago someone probably by the name of Fisher or box or something like that and
[21:15] Fisher or box or something like that and all of a sudden it kind of stuck and
[21:17] all of a sudden it kind of stuck and most statistical tests these days are
[21:19] most statistical tests these days are done to the level of significance of 5%
[21:23] done to the level of significance of 5% and that's what alpha represents there
[21:25] and that's what alpha represents there so it's essentially the probability of
[21:28] so it's essentially the probability of us being wrong in rejecting the null
[21:32] us being wrong in rejecting the null hypothesis and that's called termed a
[21:35] hypothesis and that's called termed a type 1 error we'll be looking at type 1
[21:39] type 1 error we'll be looking at type 1 and type 2 errors a little bit later on
[21:42] and type 2 errors a little bit later on in this video as well but that's what it
[21:44] in this video as well but that's what it means so what's going to happen is we
[21:46] means so what's going to happen is we can calculate this critical value this
[21:48] can calculate this critical value this point beyond which we'll be rejecting
[21:51] point beyond which we'll be rejecting the null hypothesis then calculating our
[21:54] the null hypothesis then calculating our test statistic to see where or or in
[21:57] test statistic to see where or or in other words in which side of this
[21:58] other words in which side of this critical value our test statistic lines
[22:02] critical value our test statistic lines so let's do it let's go to test
[22:05] so let's do it let's go to test statistics so as I said our sample
[22:11] statistics so as I said our sample difference is distributed normally with
[22:13] difference is distributed normally with a mean of zero and this is our variance
[22:15] a mean of zero and this is our variance P one minus P times one on n one plus
[22:18] P one minus P times one on n one plus one on n zero now if that's the case
[22:23] one on n zero now if that's the case let's consider this test statistic that
[22:26] let's consider this test statistic that we're going to call T where it's going
[22:29] we're going to call T where it's going to be the sample difference divided by
[22:32] to be the sample difference divided by the standard error of that sample
[22:34] the standard error of that sample difference so it's essentially feder hat
[22:36] difference so it's essentially feder hat divided by the square root of the
[22:38] divided by the square root of the variance
[22:41] now if theta hat itself is distributed
[22:44] now if theta hat itself is distributed normally with a mean of 0 and a variance
[22:46] normally with a mean of 0 and a variance of all this junk then T our test
[22:49] of all this junk then T our test statistic will be distributed normally
[22:52] statistic will be distributed normally with a mean of 0 and a variance of 1
[22:57] with a mean of 0 and a variance of 1 it's quite simple to prove there if you
[22:59] it's quite simple to prove there if you take the variance of this expression
[23:00] take the variance of this expression it's just going to be the variance of
[23:02] it's just going to be the variance of theta hat which is this divided by that
[23:05] theta hat which is this divided by that squared which is in fact that again so
[23:09] squared which is in fact that again so it'll cancel out and you'll get 0 and 1
[23:13] it'll cancel out and you'll get 0 and 1 and the good thing about doing that is
[23:17] and the good thing about doing that is that we've now created a very
[23:19] that we've now created a very standardized test statistic which we can
[23:22] standardized test statistic which we can compare to things like normal
[23:24] compare to things like normal distribution tables and things like that
[23:27] distribution tables and things like that another way of thinking about it is that
[23:30] another way of thinking about it is that the test statistic is just a scaled
[23:32] the test statistic is just a scaled version of the sample difference it's
[23:36] version of the sample difference it's just scaled by a factor of the standard
[23:39] just scaled by a factor of the standard deviation which is divided by the
[23:41] deviation which is divided by the standard deviation so to round that
[23:46] standard deviation so to round that point home this was the original
[23:47] point home this was the original distribution that we saw on the previous
[23:50] distribution that we saw on the previous in the previous bubble in the
[23:52] in the previous bubble in the presentation
[23:53] presentation notice that the sample difference here
[23:55] notice that the sample difference here is that difference in proportions in our
[23:58] is that difference in proportions in our sample and there's what we drew on the
[24:01] sample and there's what we drew on the previous slide as well but this axis
[24:05] previous slide as well but this axis here can be scaled so that it's the test
[24:08] here can be scaled so that it's the test statistic as well so it will - so it too
[24:12] statistic as well so it will - so it too has particular critical values beyond
[24:14] has particular critical values beyond which we're going to
[24:15] which we're going to rejecting the null hypothesis and
[24:18] rejecting the null hypothesis and because this is standardized we know
[24:20] because this is standardized we know what this critical value is when you
[24:23] what this critical value is when you have a distribution with mean zero and
[24:25] have a distribution with mean zero and variance one the critical value is 1.96
[24:30] variance one the critical value is 1.96 this critical value is the point above
[24:33] this critical value is the point above which lies 2.5% of the distribution why
[24:39] which lies 2.5% of the distribution why two point five percent well of course
[24:40] two point five percent well of course it's split in half so five percent which
[24:44] it's split in half so five percent which is our level of significance divided by
[24:46] is our level of significance divided by two is two point five percent so if we
[24:51] two is two point five percent so if we find from our sample that we get a test
[24:53] find from our sample that we get a test statistic greater than 1.96
[24:55] statistic greater than 1.96 we know we're in this rejection region
[24:58] we know we're in this rejection region in other words we know we have a sample
[25:00] in other words we know we have a sample that's too extreme to hold on to our
[25:03] that's too extreme to hold on to our null hypothesis so let's calculate that
[25:07] null hypothesis so let's calculate that test statistic the test statistic I've
[25:10] test statistic the test statistic I've used lowercase T here to represent the
[25:12] used lowercase T here to represent the actual calculated value you could do t
[25:16] actual calculated value you could do t hat if you like but that's the sample
[25:18] hat if you like but that's the sample difference divided by the square root of
[25:21] difference divided by the square root of P hat times 1 minus P hat on all that
[25:24] P hat times 1 minus P hat on all that stuff now if you recall from the actual
[25:29] stuff now if you recall from the actual sample and maybe you can cycle back 62
[25:32] sample and maybe you can cycle back 62 out of a hundred of the operative
[25:34] out of a hundred of the operative patients had improved outcomes at six
[25:38] patients had improved outcomes at six months versus 48 out of a hundred for
[25:41] months versus 48 out of a hundred for their physio only patients so this
[25:44] their physio only patients so this pooled proportion is going to be that 62
[25:48] pooled proportion is going to be that 62 plus 48 over 200 so that's 110 on 200
[25:52] plus 48 over 200 so that's 110 on 200 which is 0.55 so the pooled proportion
[25:56] which is 0.55 so the pooled proportion here is 0.55 and and one's going to be
[25:59] here is 0.55 and and one's going to be 102 or n0 I should say is also going to
[26:02] 102 or n0 I should say is also going to be a hundred and theta hat well that's
[26:06] be a hundred and theta hat well that's going to be 0.14 because that's the
[26:09] going to be 0.14 because that's the difference between the two proportions
[26:11] difference between the two proportions it was point six two minus point four
[26:15] it was point six two minus point four eight so I could have put that all on
[26:18] eight so I could have put that all on the next line but I'm running out of
[26:20] the next line but I'm running out of room here so I've just calculated that
[26:21] room here so I've just calculated that for you at one point nine nine so that
[26:25] for you at one point nine nine so that means that our calculated value of T is
[26:29] means that our calculated value of T is actually
[26:29] actually the rejection region its 1.99 versus
[26:32] the rejection region its 1.99 versus 1.96 so very close but we did manage to
[26:36] 1.96 so very close but we did manage to get it in the rejection region so if we
[26:39] get it in the rejection region so if we zoom in here that's going to be 1.96 and
[26:43] zoom in here that's going to be 1.96 and our little test statistic lies somewhere
[26:47] our little test statistic lies somewhere there that little orange triangle so
[26:51] there that little orange triangle so what does that mean well it means we can
[26:55] what does that mean well it means we can reject our null hypothesis so there's
[27:01] reject our null hypothesis so there's enough evidence to infer a difference
[27:02] enough evidence to infer a difference between the true treatment options now
[27:08] between the true treatment options now the important thing here is that there's
[27:09] the important thing here is that there's a specific level of significance we've
[27:11] a specific level of significance we've used which is the 5% level of
[27:14] used which is the 5% level of significance the test would be
[27:16] significance the test would be completely different had we used to say
[27:18] completely different had we used to say a 1% level of significance that just
[27:22] a 1% level of significance that just means we're going to need to have a test
[27:23] means we're going to need to have a test statistic that's more extreme to reject
[27:26] statistic that's more extreme to reject the null hypothesis in that case it's
[27:28] the null hypothesis in that case it's probably not going to reject so this
[27:32] probably not going to reject so this fairly arbitrary value we select our
[27:34] fairly arbitrary value we select our strictness strictness of the hypothesis
[27:39] strictness strictness of the hypothesis test is actually quite important here
[27:41] test is actually quite important here and our decision hinges on what level of
[27:46] and our decision hinges on what level of significance we've chosen but yes
[27:48] significance we've chosen but yes welcome to hypothesis testing nothing
[27:51] welcome to hypothesis testing nothing nothing is ever proven it's only ever
[27:55] nothing is ever proven it's only ever inferred and I think maybe that's a good
[27:57] inferred and I think maybe that's a good little takeaway from this point as well
[27:59] little takeaway from this point as well never use the word prove or disprove
[28:01] never use the word prove or disprove because you can't do that in stats the
[28:04] because you can't do that in stats the only thing you can do is infer and in
[28:07] only thing you can do is infer and in this case we can infer a difference
[28:10] this case we can infer a difference between the two treatment options
[28:12] between the two treatment options it means our sample difference happen to
[28:15] it means our sample difference happen to be extreme enough for us to suggest that
[28:18] be extreme enough for us to suggest that in this case the operative patients did
[28:21] in this case the operative patients did better than the physio only patients
[28:27] so let's have a little chew on p-value now the p-value is the proportion of
[28:34] now the p-value is the proportion of repeated samples under the null
[28:36] repeated samples under the null hypothesis that would be as extreme as
[28:40] hypothesis that would be as extreme as the test statistic we generated okay
[28:43] the test statistic we generated okay that seems like a mouthful but let's
[28:44] that seems like a mouthful but let's read it again the p-value is the
[28:45] read it again the p-value is the proportion of repeated samples under the
[28:48] proportion of repeated samples under the null hypothesis that would be as extreme
[28:51] null hypothesis that would be as extreme as the test statistic we generated so
[28:56] as the test statistic we generated so again like the previous two slides we
[28:59] again like the previous two slides we assume the null hypothesis is true so
[29:02] assume the null hypothesis is true so the true difference is zero meaning that
[29:04] the true difference is zero meaning that our expected sample difference is also
[29:06] our expected sample difference is also zero the center of the distribution in
[29:09] zero the center of the distribution in other words is zero and of course when
[29:13] other words is zero and of course when we scale it to this test to this test
[29:16] we scale it to this test to this test statistic at T the center of that
[29:18] statistic at T the center of that distribution will also be zero and our
[29:21] distribution will also be zero and our alternate hypothesis is that the
[29:23] alternate hypothesis is that the difference is non zero so here's the
[29:26] difference is non zero so here's the probability distribution again with
[29:28] probability distribution again with alpha being 0.05 and it's centered on
[29:32] alpha being 0.05 and it's centered on zero because we assume the null
[29:34] zero because we assume the null hypothesis is true we found a test
[29:38] hypothesis is true we found a test statistic of 1.99 which was just a shade
[29:41] statistic of 1.99 which was just a shade to the right of this yellow bar here so
[29:44] to the right of this yellow bar here so we're just in the rejection region what
[29:47] we're just in the rejection region what a p-value is is the remaining shaded
[29:51] a p-value is is the remaining shaded region beyond our test statistic what
[29:55] region beyond our test statistic what this red section is is the number of
[30:00] this red section is is the number of repeated samples under the null
[30:02] repeated samples under the null hypothesis so assuming the null
[30:04] hypothesis so assuming the null hypothesis is true it's the proportion
[30:07] hypothesis is true it's the proportion of samples that would have a more
[30:09] of samples that would have a more extreme test statistic than ours or I
[30:13] extreme test statistic than ours or I should say a test statistic which is as
[30:15] should say a test statistic which is as extreme or more extreme than ours so our
[30:19] extreme or more extreme than ours so our the sample was extreme enough for us to
[30:21] the sample was extreme enough for us to reject the null hypothesis but there
[30:23] reject the null hypothesis but there would be some samples that are even more
[30:25] would be some samples that are even more extreme this red section summarizes all
[30:28] extreme this red section summarizes all of those possible samples and if you
[30:31] of those possible samples and if you were to add up that whole red section as
[30:33] were to add up that whole red section as a proportion of this distribution it's
[30:37] a proportion of this distribution it's going to be 0.04 7
[30:40] going to be 0.04 7 now it's actually very difficult to
[30:41] now it's actually very difficult to calculate that by hand a computer
[30:43] calculate that by hand a computer program can do it for the purpose of
[30:45] program can do it for the purpose of this let's not worry about how that's
[30:47] this let's not worry about how that's calculated but you were probably going
[30:50] calculated but you were probably going to guess that it was going to be
[30:51] to guess that it was going to be something very close to 0.05 right we
[30:55] something very close to 0.05 right we only just rejected the null hypothesis
[30:58] only just rejected the null hypothesis from this test statistic here so the
[31:01] from this test statistic here so the p-value had to be pretty close to 0.05
[31:03] p-value had to be pretty close to 0.05 and in fact it had to be just slightly
[31:05] and in fact it had to be just slightly less than 0.05 that shaded red region
[31:08] less than 0.05 that shaded red region would be slightly less than the shaded
[31:10] would be slightly less than the shaded yellow region which is exactly 0.05
[31:17] hopefully you can see the relationship between P and alpha if your p-value is
[31:22] between P and alpha if your p-value is less than alpha then there's enough
[31:24] less than alpha then there's enough evidence to reject the null hypothesis a
[31:27] evidence to reject the null hypothesis a means that our test statistic then must
[31:29] means that our test statistic then must be in the rejection region if P is
[31:34] be in the rejection region if P is greater than alpha then there's not
[31:35] greater than alpha then there's not enough evidence to reject the null
[31:37] enough evidence to reject the null hypothesis so the p-value is a really
[31:40] hypothesis so the p-value is a really quick way of looking at how extreme our
[31:42] quick way of looking at how extreme our sample is given the null hypothesis is
[31:45] sample is given the null hypothesis is true so obviously if your p-value is
[31:48] true so obviously if your p-value is very very low very very close to zero
[31:51] very very low very very close to zero you're saying that or it's really
[31:54] you're saying that or it's really unlikely to get a sample more extreme
[31:57] unlikely to get a sample more extreme than ours right so in this case as P is
[32:01] than ours right so in this case as P is 0.04 7 that's a bit of a typo there that
[32:05] 0.04 7 that's a bit of a typo there that should say 0.05 so with your mental
[32:09] should say 0.05 so with your mental powers turn that into a 0.05 please as
[32:13] powers turn that into a 0.05 please as the p-value is less than 0.05 we can
[32:16] the p-value is less than 0.05 we can reject the null hypothesis at the 5%
[32:18] reject the null hypothesis at the 5% level of significance and say there's
[32:20] level of significance and say there's enough evidence to suggest a difference
[32:22] enough evidence to suggest a difference in proportions P 1 and P naught so the
[32:28] in proportions P 1 and P naught so the good thing about p-values is that you
[32:29] good thing about p-values is that you can save you the trouble of going to of
[32:31] can save you the trouble of going to of doing separate hypothesis tests for
[32:34] doing separate hypothesis tests for different levels of significance so we
[32:37] different levels of significance so we know because the p-value is 0.04 7 that
[32:40] know because the p-value is 0.04 7 that we're going to reject the null
[32:42] we're going to reject the null hypothesis if the level of significance
[32:44] hypothesis if the level of significance is 5% but we're not going to reject a
[32:49] is 5% but we're not going to reject a null hypothesis if the level of
[32:51] null hypothesis if the level of significance was 1%
[32:53] significance was 1% because if we're being strict about
[32:55] because if we're being strict about whether we reject the null hypothesis
[32:58] whether we reject the null hypothesis and this yellow region becomes a lot
[33:00] and this yellow region becomes a lot less our test statistic will now no
[33:05] less our test statistic will now no longer lie in that rejection region so
[33:12] longer lie in that rejection region so yes as I said hopefully you're realizing
[33:14] yes as I said hopefully you're realizing that all three of these concepts are
[33:15] that all three of these concepts are related the null hypothesis well four of
[33:18] related the null hypothesis well four of the concepts if you include these as two
[33:20] the concepts if you include these as two separate concepts the null hypothesis
[33:23] separate concepts the null hypothesis your level of significance your test
[33:26] your level of significance your test statistic and p-value there like for
[33:27] statistic and p-value there like for moving parts if you move one the others
[33:30] moving parts if you move one the others must shift and they all have the same
[33:32] must shift and they all have the same common feature of assuming the null
[33:35] common feature of assuming the null hypothesis is true or I should say the
[33:38] hypothesis is true or I should say the perspective being that null hypothesis
[33:41] perspective being that null hypothesis all right so let's now take a look at
[33:44] all right so let's now take a look at confidence intervals so as I've written
[33:48] confidence intervals so as I've written here confidence intervals are
[33:49] here confidence intervals are constructed around the sample statistic
[33:51] constructed around the sample statistic theta hat or alternatively the
[33:54] theta hat or alternatively the calculated test statistic T so what this
[33:57] calculated test statistic T so what this means is that we now have a perspective
[33:59] means is that we now have a perspective which is not the null hypothesis our
[34:02] which is not the null hypothesis our perspective is what we calculate from
[34:03] perspective is what we calculate from the sample itself now the distinction
[34:07] the sample itself now the distinction here between theta hat and calculated
[34:10] here between theta hat and calculated test statistic T is only one other scale
[34:14] test statistic T is only one other scale and we saw that a few slides ago but
[34:17] and we saw that a few slides ago but they're basically calculating or they're
[34:19] they're basically calculating or they're they're measuring the same thing but
[34:20] they're measuring the same thing but just on a different scale so you can
[34:24] just on a different scale so you can construct a confidence interval around
[34:26] construct a confidence interval around the calculated test statistic as well
[34:28] the calculated test statistic as well but perhaps more commonly we just take
[34:31] but perhaps more commonly we just take the sample statistic which is our sample
[34:33] the sample statistic which is our sample proportion or sample mean and then we
[34:37] proportion or sample mean and then we can construct a confidence interval
[34:39] can construct a confidence interval around that so in our case we have a
[34:42] around that so in our case we have a sample statistic theta hat which was
[34:44] sample statistic theta hat which was 0.14 remember that the proportion of
[34:47] 0.14 remember that the proportion of those having the surgery that had
[34:50] those having the surgery that had positive outcomes was 0.62 and the
[34:53] positive outcomes was 0.62 and the proportion of those with the physio only
[34:54] proportion of those with the physio only group getting successful outcomes was
[34:57] group getting successful outcomes was 0.48 so the difference there's 0.14 and
[34:59] 0.48 so the difference there's 0.14 and we can construct an interval around that
[35:01] we can construct an interval around that point 1/4 which will exist independently
[35:05] point 1/4 which will exist independently of the null hypothesis
[35:07] of the null hypothesis now to construct an interval around this
[35:10] now to construct an interval around this particular value we need to know what
[35:12] particular value we need to know what this standard error is of this measure
[35:14] this standard error is of this measure theta hat so what's the standard error
[35:17] theta hat so what's the standard error of theta hat
[35:18] of theta hat well feet is just the difference between
[35:22] well feet is just the difference between two proportions so the standard error is
[35:24] two proportions so the standard error is going to be the sum of all this junk
[35:26] going to be the sum of all this junk here and we can sub in the values that
[35:29] here and we can sub in the values that we got from our sample so 0.62 is p1
[35:31] we got from our sample so 0.62 is p1 with a hat on it point four eight is P
[35:34] with a hat on it point four eight is P naught with a hat on it and then N 1 and
[35:37] naught with a hat on it and then N 1 and N naught are both 100 so in summing
[35:40] N naught are both 100 so in summing those values in we'll get a sense of the
[35:42] those values in we'll get a sense of the variation of our theta hat measure and
[35:45] variation of our theta hat measure and that is the standard error if you sub
[35:49] that is the standard error if you sub everything in you get zero point zero
[35:50] everything in you get zero point zero six nine seven so with that we can now
[35:55] six nine seven so with that we can now construct a confidence interval and
[35:57] construct a confidence interval and here's a 95% confidence interval we take
[36:00] here's a 95% confidence interval we take our theta hat and we add and subtract
[36:02] our theta hat and we add and subtract that standard error times that factor
[36:06] that standard error times that factor from the normal distribution because we
[36:08] from the normal distribution because we know due to the central limit theorem
[36:10] know due to the central limit theorem that this theta hat is going to be
[36:13] that this theta hat is going to be distributed normally in large samples at
[36:16] distributed normally in large samples at least at Shelby so we add and subtract
[36:19] least at Shelby so we add and subtract the appropriate value from these air
[36:21] the appropriate value from these air distribution times the standard error
[36:23] distribution times the standard error and I've written here 0.975 because
[36:28] and I've written here 0.975 because don't forget for a 95% confidence
[36:30] don't forget for a 95% confidence interval there's gonna be 2.5 percent in
[36:33] interval there's gonna be 2.5 percent in each of the tails of the distribution
[36:36] each of the tails of the distribution and if we add and subtract that value we
[36:39] and if we add and subtract that value we get an interval which is 0.0035 zero
[36:42] get an interval which is 0.0035 zero point two seven six five and to
[36:46] point two seven six five and to interpret that we can say we are 95%
[36:48] interpret that we can say we are 95% confident that the interval from zero
[36:50] confident that the interval from zero point three five percent I've just
[36:52] point three five percent I've just converted that to a percent to twenty
[36:54] converted that to a percent to twenty seven point six five percent contains
[36:56] seven point six five percent contains the true population difference theta now
[37:00] the true population difference theta now I think this is probably the best way of
[37:01] I think this is probably the best way of describing a confidence interval you
[37:05] describing a confidence interval you might be tempted to say something like
[37:06] might be tempted to say something like we're 95% confident that the true
[37:08] we're 95% confident that the true population difference lies between these
[37:10] population difference lies between these two values my subtle gripe with that
[37:15] two values my subtle gripe with that phrasing is that you're insinuating that
[37:17] phrasing is that you're insinuating that the population difference is a variable
[37:19] the population difference is a variable where we know the
[37:21] where we know the population difference theta is a fixed
[37:23] population difference theta is a fixed value so saying at the way I've said it
[37:26] value so saying at the way I've said it here is maybe a bit lighter on that and
[37:29] here is maybe a bit lighter on that and so you say you're basically saying that
[37:30] so you say you're basically saying that we're 95% confident that the interval
[37:33] we're 95% confident that the interval overlaps this fixed value anyway that's
[37:37] overlaps this fixed value anyway that's for the sticklers out there but as you
[37:41] for the sticklers out there but as you can see we've basically constructed an
[37:43] can see we've basically constructed an interval around the sample estimate so
[37:47] interval around the sample estimate so what's significant treatment difference
[37:49] what's significant treatment difference all about well remember Part B said the
[37:53] all about well remember Part B said the orthopedic Society requires an outcome
[37:55] orthopedic Society requires an outcome improvement of at least five percent
[37:57] improvement of at least five percent before updating treatment protocols now
[38:00] before updating treatment protocols now the hypothesis we tested here was that
[38:02] the hypothesis we tested here was that theta was different from zero
[38:04] theta was different from zero that was our alternate hypothesis that's
[38:06] that was our alternate hypothesis that's what we were trying to seek evidence for
[38:09] what we were trying to seek evidence for but in reality what the orthopedic
[38:12] but in reality what the orthopedic Society wants us to do is to run a
[38:14] Society wants us to do is to run a hypothesis test that might look a little
[38:16] hypothesis test that might look a little bit like this we're seeking evidence for
[38:20] bit like this we're seeking evidence for the true population difference to be
[38:22] the true population difference to be greater than 0.05 greater than a five
[38:26] greater than 0.05 greater than a five percent difference so it's a slightly
[38:29] percent difference so it's a slightly different hypothesis that we're running
[38:31] different hypothesis that we're running nonetheless we can use what we've just
[38:34] nonetheless we can use what we've just done we can use the original hypothesis
[38:36] done we can use the original hypothesis test and look at the p-values but and
[38:38] test and look at the p-values but and look at the confidence interval to
[38:40] look at the confidence interval to assess whether we'd reject this
[38:43] assess whether we'd reject this secondary hypothesis test so what do I
[38:47] secondary hypothesis test so what do I mean by that well let's have a look at
[38:49] mean by that well let's have a look at the p-value we got we were testing the
[38:52] the p-value we got we were testing the null hypothesis that theta was equal to
[38:54] null hypothesis that theta was equal to zero and this plot is going to show us
[38:57] zero and this plot is going to show us the confidence interval associated with
[39:00] the confidence interval associated with this treatment difference so recall that
[39:04] this treatment difference so recall that it went from about 0.3% to 27% something
[39:07] it went from about 0.3% to 27% something like that so very close to zero but this
[39:10] like that so very close to zero but this represents a 95% confidence interval for
[39:13] represents a 95% confidence interval for the true treatment difference now here
[39:17] the true treatment difference now here I'm going to provide you with four other
[39:18] I'm going to provide you with four other theoretical samples to say we did four
[39:21] theoretical samples to say we did four more samples and these were our
[39:23] more samples and these were our confidence intervals you can see that if
[39:25] confidence intervals you can see that if the p-values say 0.58 it's going to be
[39:29] the p-values say 0.58 it's going to be crossing zero
[39:31] crossing zero we know that for sure because that's
[39:32] we know that for sure because that's greater than 0.05 anytime the p value is
[39:36] greater than 0.05 anytime the p value is more than 0.05 we know it must cross
[39:40] more than 0.05 we know it must cross zero this confidence interval and so the
[39:42] zero this confidence interval and so the same goes here with another sample that
[39:44] same goes here with another sample that gave us a p-value of 0.06 for it's quite
[39:46] gave us a p-value of 0.06 for it's quite close to 0.05 but it's still greater
[39:49] close to 0.05 but it's still greater than 0.05 so we know this confidence
[39:52] than 0.05 so we know this confidence interval must cross zero our sample
[39:56] interval must cross zero our sample didn't cross zero but only just
[39:58] didn't cross zero but only just say we have another one with the p-value
[40:00] say we have another one with the p-value of 0.02 and it's a very this could be a
[40:04] of 0.02 and it's a very this could be a very large sample for example but it
[40:07] very large sample for example but it would have a very small confidence
[40:09] would have a very small confidence interval here nonetheless it's it's
[40:11] interval here nonetheless it's it's confined to one side of 0 and finally we
[40:14] confined to one side of 0 and finally we have this test which is again all on one
[40:17] have this test which is again all on one side of 0 the p-value is very very very
[40:19] side of 0 the p-value is very very very low indeed so in which of these samples
[40:24] low indeed so in which of these samples do you think will the orthopedic society
[40:26] do you think will the orthopedic society be comfortable that the improvement is
[40:28] be comfortable that the improvement is at least 5% he is 5% if I was to draw a
[40:33] at least 5% he is 5% if I was to draw a line at 5% you can see that it's only
[40:38] line at 5% you can see that it's only this final sample where we're confident
[40:41] this final sample where we're confident with our 95% confidence interval that
[40:44] with our 95% confidence interval that it's all on one side of this 5%
[40:46] it's all on one side of this 5% difference our sample certainly doesn't
[40:50] difference our sample certainly doesn't achieve that even though we could be
[40:51] achieve that even though we could be confident that the true treatment
[40:54] confident that the true treatment difference was greater than 0 we
[40:57] difference was greater than 0 we couldn't be confident at the 95% level
[40:59] couldn't be confident at the 95% level that the treatment difference is greater
[41:02] that the treatment difference is greater than 5% you can see it crosses over 5%
[41:05] than 5% you can see it crosses over 5% so that's why looking at confidence
[41:07] so that's why looking at confidence intervals as a little bit more malleable
[41:08] intervals as a little bit more malleable than your hypothesis test because that
[41:11] than your hypothesis test because that only gives you the outcome of one
[41:13] only gives you the outcome of one hypothesis that you're testing but here
[41:15] hypothesis that you're testing but here we can just look at this we can look at
[41:17] we can just look at this we can look at our test statistic create our interval
[41:19] our test statistic create our interval and say you know what the orthopedic
[41:22] and say you know what the orthopedic Society won't be satisfied that the true
[41:24] Society won't be satisfied that the true treatment difference is greater than 5%
[41:27] treatment difference is greater than 5% even though we're confident that
[41:29] even though we're confident that operative treatment does better than
[41:32] operative treatment does better than non-operative treatment so interestingly
[41:35] non-operative treatment so interestingly the way I've constructed this you can
[41:36] the way I've constructed this you can see that the p-value of 0.002 this
[41:38] see that the p-value of 0.002 this sample here
[41:41] sample here it's treatment difference was say on
[41:43] it's treatment difference was say on average say 2.5
[41:45] average say 2.5 and it's confined within this narrow
[41:47] and it's confined within this narrow region so we can actually be confident
[41:50] region so we can actually be confident here that the true treatment difference
[41:52] here that the true treatment difference is greater than zero but less than five
[41:54] is greater than zero but less than five now the only way that happens is if your
[41:56] now the only way that happens is if your sample size is really really large and
[41:58] sample size is really really large and perhaps that's what happens with this
[42:00] perhaps that's what happens with this particular sample we become a lot more
[42:03] particular sample we become a lot more confident of where the true treatment
[42:05] confident of where the true treatment difference is so in this case the
[42:07] difference is so in this case the orthopedic orthopedic Society would say
[42:09] orthopedic orthopedic Society would say well that's good information to know and
[42:11] well that's good information to know and we will not be recommending surgery here
[42:13] we will not be recommending surgery here because we know well we can infer that
[42:16] because we know well we can infer that the true improvement for surgery over
[42:18] the true improvement for surgery over the non surgery treatments is less than
[42:22] the non surgery treatments is less than five percent all right let's have a look
[42:27] five percent all right let's have a look at power and sample size now which is my
[42:29] at power and sample size now which is my sort of favorite section really so
[42:37] sort of favorite section really so before we get into any calculations
[42:40] before we get into any calculations we're gonna have a look at this
[42:41] we're gonna have a look at this two-by-two table now you might have seen
[42:45] two-by-two table now you might have seen this before but if the null hypothesis
[42:48] this before but if the null hypothesis is true in other words there's no effect
[42:50] is true in other words there's no effect or no difference between the two groups
[42:52] or no difference between the two groups we can either do one of two things we
[42:55] we can either do one of two things we can either have a hypothesis test that
[42:57] can either have a hypothesis test that rejects the null hypothesis or that
[42:59] rejects the null hypothesis or that doesn't reject the null hypothesis and
[43:02] doesn't reject the null hypothesis and if the null hypothesis is in fact true
[43:05] if the null hypothesis is in fact true we would hope that we don't reject it
[43:07] we would hope that we don't reject it right it would be wrong of us to reject
[43:11] right it would be wrong of us to reject the null hypothesis but nonetheless we
[43:12] the null hypothesis but nonetheless we could possibly be doing that so if we
[43:15] could possibly be doing that so if we run our hypothesis test and end up not
[43:17] run our hypothesis test and end up not rejecting that's called a true negative
[43:20] rejecting that's called a true negative and the probability of that is given by
[43:23] and the probability of that is given by 1 minus alpha we actually know what the
[43:25] 1 minus alpha we actually know what the probability of this is we set the
[43:27] probability of this is we set the probability of this outcome and we also
[43:30] probability of this outcome and we also set the probability of having a false
[43:32] set the probability of having a false positive what's called a type 1 error
[43:34] positive what's called a type 1 error where we reject a null hypothesis that
[43:36] where we reject a null hypothesis that happens to be true
[43:38] happens to be true and we usually set that to 5% but of
[43:40] and we usually set that to 5% but of course you can set that to 1% or 10% but
[43:45] course you can set that to 1% or 10% but what happens if the null hypothesis is
[43:47] what happens if the null hypothesis is false so in the event that it's false if
[43:50] false so in the event that it's false if we don't reject it that's called a false
[43:52] we don't reject it that's called a false negative in other words that's a type 2
[43:55] negative in other words that's a type 2 error which we can deem beta
[43:58] error which we can deem beta again we hope we don't do this we hope
[44:00] again we hope we don't do this we hope that if the null hypothesis is false in
[44:03] that if the null hypothesis is false in other words there is an effect or a
[44:04] other words there is an effect or a difference between the two groups we
[44:08] difference between the two groups we hope that we reject that and in that
[44:10] hope that we reject that and in that circumstance we can say that's a true
[44:11] circumstance we can say that's a true positive which happens to be one minus
[44:13] positive which happens to be one minus beta and that's called power so the
[44:16] beta and that's called power so the power of the model is the probability of
[44:20] power of the model is the probability of rejecting of false null hypothesis in
[44:23] rejecting of false null hypothesis in other words it's the ability of a model
[44:25] other words it's the ability of a model to detect a specified difference but
[44:30] to detect a specified difference but let's see how that interacts let's see
[44:31] let's see how that interacts let's see what happens with specified differences
[44:33] what happens with specified differences that are larger and smaller so this is
[44:36] that are larger and smaller so this is where it gets a little bit interesting
[44:39] where it gets a little bit interesting this plot here is for our sample
[44:41] this plot here is for our sample difference - theta hat right let's zoom
[44:45] difference - theta hat right let's zoom in a little bit if we assume that theta
[44:48] in a little bit if we assume that theta is equal to zero so that there is no
[44:51] is equal to zero so that there is no difference between the two groups our
[44:53] difference between the two groups our test statistic would be in this
[44:55] test statistic would be in this distribution here this black and
[44:56] distribution here this black and distribution here but of course when we
[44:59] distribution here but of course when we construct the hypothesis test we have an
[45:02] construct the hypothesis test we have an inkling that there might be some
[45:03] inkling that there might be some difference between the two groups we
[45:05] difference between the two groups we have an inkling that operative patients
[45:07] have an inkling that operative patients might do better than those that receive
[45:10] might do better than those that receive physio only treatment so there's this
[45:14] physio only treatment so there's this theoretical difference between the two
[45:17] theoretical difference between the two groups which were going to label Delta
[45:19] groups which were going to label Delta here the Greek letter Delta now this
[45:22] here the Greek letter Delta now this plot really provided for me when I it
[45:25] plot really provided for me when I it was only when I started teaching this
[45:27] was only when I started teaching this particular topic that I saw this plot
[45:30] particular topic that I saw this plot and it just rammed home what the power
[45:33] and it just rammed home what the power of a statistical test was all about so
[45:36] of a statistical test was all about so bear with me remember from the first
[45:38] bear with me remember from the first part of this test if we assume that the
[45:41] part of this test if we assume that the null hypothesis is true we construct
[45:45] null hypothesis is true we construct this rejection region let's call it
[45:46] this rejection region let's call it alpha now if it's a one tailed test like
[45:49] alpha now if it's a one tailed test like perhaps it is here alpha is only on one
[45:52] perhaps it is here alpha is only on one side here and say that's 5% then this
[45:54] side here and say that's 5% then this will be 5% the yellow proportion of the
[45:57] will be 5% the yellow proportion of the whole black curve here now that's all
[46:00] whole black curve here now that's all well and good we can run our hypothesis
[46:02] well and good we can run our hypothesis test see where our test statistic lies
[46:04] test see where our test statistic lies and if it's in that yellow region we'll
[46:06] and if it's in that yellow region we'll reject the null hypothesis but if indeed
[46:09] reject the null hypothesis but if indeed this red distribution is
[46:11] this red distribution is where the data is we're probably more
[46:14] where the data is we're probably more likely than not to reject the null
[46:16] likely than not to reject the null hypothesis right most of the
[46:17] hypothesis right most of the distribution is in this rejection region
[46:19] distribution is in this rejection region so we've set up the null hypothesis
[46:22] so we've set up the null hypothesis essentially to fail right that's the
[46:24] essentially to fail right that's the whole point we set up this null
[46:25] whole point we set up this null hypothesis and kind of hope that it
[46:27] hypothesis and kind of hope that it fails if we're trying to if we're really
[46:30] fails if we're trying to if we're really seeking evidence to show there's a
[46:31] seeking evidence to show there's a difference and if the difference is size
[46:34] difference and if the difference is size Delta in reality more likely than not we
[46:37] Delta in reality more likely than not we are going to reject the null hypothesis
[46:38] are going to reject the null hypothesis unless we end up getting a sample in
[46:41] unless we end up getting a sample in this part of the distribution to the
[46:43] this part of the distribution to the left of this black line if we're in this
[46:45] left of this black line if we're in this part of the distribution it just so
[46:47] part of the distribution it just so happens that we will not reject the null
[46:49] happens that we will not reject the null hypothesis so that is going to be our
[46:52] hypothesis so that is going to be our area beta so while alpha is something
[46:55] area beta so while alpha is something that we create for ourselves arbitrarily
[46:58] that we create for ourselves arbitrarily but we select say 0.05 because it's nice
[47:00] but we select say 0.05 because it's nice and round we select that for ourselves
[47:02] and round we select that for ourselves but beta actually depends on quite a lot
[47:05] but beta actually depends on quite a lot of factors it depends on alpha but it
[47:08] of factors it depends on alpha but it also depends on how far away these two
[47:12] also depends on how far away these two curves are so what the theorized
[47:14] curves are so what the theorized difference is going to be and it also
[47:16] difference is going to be and it also depends on how skinny each of these two
[47:18] depends on how skinny each of these two distributions are as well but I'll talk
[47:21] distributions are as well but I'll talk a bit more about that in a moment but
[47:24] a bit more about that in a moment but what happens then if that's beta is that
[47:26] what happens then if that's beta is that the power of our test is one minus beta
[47:29] the power of our test is one minus beta and that's given by this green section
[47:33] and that's given by this green section here so if indeed there's a true
[47:35] here so if indeed there's a true difference Delta this green section here
[47:38] difference Delta this green section here is the power of our model to reject a
[47:42] is the power of our model to reject a false null hypothesis so you can see
[47:45] false null hypothesis so you can see that how it was a three step process we
[47:47] that how it was a three step process we first needed to figure out what was the
[47:49] first needed to figure out what was the rejection region for the boring old
[47:52] rejection region for the boring old hypothesis test then we were like
[47:54] hypothesis test then we were like alright if there is this actual
[47:56] alright if there is this actual difference in reality what chance do we
[47:58] difference in reality what chance do we have of really rejecting that null
[48:00] have of really rejecting that null hypothesis and the chance of that is 1
[48:03] hypothesis and the chance of that is 1 minus beta ok now looking at this
[48:08] minus beta ok now looking at this section we're calling power here think
[48:11] section we're calling power here think about what happens if the theorized
[48:14] about what happens if the theorized difference is enlarged so let's just say
[48:19] difference is enlarged so let's just say that we thought the operative group was
[48:20] that we thought the operative group was in reality going to do much better than
[48:23] in reality going to do much better than the non-operative group
[48:25] the non-operative group but what happens is that these two
[48:27] but what happens is that these two curves get separated imagine you just
[48:29] curves get separated imagine you just kind of pushed these two curves apart
[48:30] kind of pushed these two curves apart you'll see then that beta the area that
[48:34] you'll see then that beta the area that we're calling beta here is going to
[48:35] we're calling beta here is going to become a lot smaller and the area that's
[48:37] become a lot smaller and the area that's 1 minus beta is actually become a lot
[48:39] 1 minus beta is actually become a lot larger more of the proportion of this
[48:41] larger more of the proportion of this distribution is going to lie to the
[48:43] distribution is going to lie to the right of this black line so if the
[48:47] right of this black line so if the difference that we're theorizing is true
[48:49] difference that we're theorizing is true in the population gets larger we're
[48:51] in the population gets larger we're going to become more likely to find it
[48:54] going to become more likely to find it more likely to reject that null
[48:57] more likely to reject that null hypothesis but if the theorized
[48:59] hypothesis but if the theorized difference is very very small then these
[49:02] difference is very very small then these two groups are going to be quite close
[49:03] two groups are going to be quite close together these two and bell curves have
[49:06] together these two and bell curves have will be quite close together and it'll
[49:08] will be quite close together and it'll become less likely to reject the null
[49:10] become less likely to reject the null hypothesis so you're less likely to find
[49:12] hypothesis so you're less likely to find the difference if the difference in
[49:15] the difference if the difference in reality is smaller and the second point
[49:17] reality is smaller and the second point to note is for a given different so
[49:19] to note is for a given different so let's just presume this difference is
[49:21] let's just presume this difference is Delta here what happens if you make each
[49:23] Delta here what happens if you make each of these two curves skinnier think about
[49:27] of these two curves skinnier think about it you're squeezing this black curve
[49:29] it you're squeezing this black curve together and squeezing this red curve
[49:32] together and squeezing this red curve together but keeping their centers the
[49:34] together but keeping their centers the same so imagine you take your hands into
[49:36] same so imagine you take your hands into the distribution and squeeze them both
[49:38] the distribution and squeeze them both together again the proportion of the
[49:40] together again the proportion of the distribution to the right of that black
[49:42] distribution to the right of that black line is going to increase right you're
[49:45] line is going to increase right you're squeezing out this beta area such that
[49:48] squeezing out this beta area such that most of this curve now is going to be 1
[49:50] most of this curve now is going to be 1 minus beta well what am i implying when
[49:53] minus beta well what am i implying when I say we're making the curves skinnier
[49:55] I say we're making the curves skinnier well I'm implying that the sample size
[49:58] well I'm implying that the sample size is increasing so when your sample size
[50:01] is increasing so when your sample size increases don't forget the variance of
[50:03] increases don't forget the variance of each of these remember how we calculated
[50:04] each of these remember how we calculated the variance of these it always had some
[50:06] the variance of these it always had some kind of divided by n on it divided by
[50:09] kind of divided by n on it divided by root n so in the sample size increases
[50:12] root n so in the sample size increases these two curves are going to get a lot
[50:14] these two curves are going to get a lot skinnier for a given difference and in
[50:17] skinnier for a given difference and in doing so you're going to become more
[50:18] doing so you're going to become more likely to reject that null hypothesis if
[50:21] likely to reject that null hypothesis if indeed there's a difference so how do we
[50:24] indeed there's a difference so how do we summarize that the power will increase
[50:26] summarize that the power will increase for an increasing difference and the
[50:31] for an increasing difference and the power will also increase for an
[50:33] power will also increase for an increasing sample size over a given
[50:35] increasing sample size over a given difference
[50:38] so now we're going to have a look at example 2 which will give us a chance to
[50:42] example 2 which will give us a chance to put into practice some of that stuff
[50:44] put into practice some of that stuff we've just learned on power and sample
[50:46] we've just learned on power and sample size now be warned it's going to get a
[50:50] size now be warned it's going to get a little ugly in terms of algebra but this
[50:52] little ugly in terms of algebra but this is a really good chance to sort of reel
[50:54] is a really good chance to sort of reel to really nail down some of these
[50:55] to really nail down some of these concepts so I'm not too concerned that
[50:58] concepts so I'm not too concerned that it might be a little a little fresh when
[51:00] it might be a little a little fresh when it comes to algebra here but to operate
[51:03] it comes to algebra here but to operate or not to operate it's another in the
[51:05] or not to operate it's another in the same sort of vein as our first example
[51:08] same sort of vein as our first example this wants to do with ankle fractures in
[51:10] this wants to do with ankle fractures in children and again the theory in real
[51:13] children and again the theory in real life is that ankle fractures in young
[51:17] life is that ankle fractures in young patients may heal of their own accord
[51:20] patients may heal of their own accord once they um get some physio and things
[51:22] once they um get some physio and things like that this might not be a need for
[51:24] like that this might not be a need for putting them under the knife but here we
[51:27] putting them under the knife but here we have a sample of 800 children with ankle
[51:30] have a sample of 800 children with ankle fracture that's a lot of ankles
[51:31] fracture that's a lot of ankles fractured where 400 are provided an
[51:34] fractured where 400 are provided an operative treatment and 400 are provided
[51:37] operative treatment and 400 are provided physio only the outcome of interest is
[51:40] physio only the outcome of interest is the ability of the child to walk
[51:42] the ability of the child to walk normally at 3 months ok so the first
[51:48] normally at 3 months ok so the first question we're going to ask is what
[51:49] question we're going to ask is what power will a hypothesis test possess to
[51:53] power will a hypothesis test possess to detect a 10% improvement in the
[51:55] detect a 10% improvement in the operative cohort if we assume 50% of the
[51:59] operative cohort if we assume 50% of the physio only cohort will walk normally at
[52:01] physio only cohort will walk normally at 3 months so there's the detectable
[52:05] 3 months so there's the detectable difference 10% so so what power will
[52:08] difference 10% so so what power will this hypothesis test have to find that
[52:11] this hypothesis test have to find that difference if indeed in the operative
[52:14] difference if indeed in the operative cohort say 60% will walk normally at 3
[52:17] cohort say 60% will walk normally at 3 months so where I say a 10% improvement
[52:19] months so where I say a 10% improvement here I mean from 50% to 60% what power
[52:23] here I mean from 50% to 60% what power will our hypothesis test have to detect
[52:25] will our hypothesis test have to detect such a difference and I'm saying to use
[52:28] such a difference and I'm saying to use a one-tailed hypothesis test here so
[52:32] a one-tailed hypothesis test here so we're only really interested in that one
[52:34] we're only really interested in that one direction where the operative cohort
[52:36] direction where the operative cohort does better than the non operative than
[52:39] does better than the non operative than the physio only cohort so that's part A
[52:44] the physio only cohort so that's part A Part B will actually get a chance to
[52:47] Part B will actually get a chance to calculate a sample size given
[52:50] calculate a sample size given power so you can see that in the
[52:52] power so you can see that in the question we got it given a sample size
[52:54] question we got it given a sample size of well 800 400 and each cohort in Part
[52:58] of well 800 400 and each cohort in Part B here were asked to relax that and I'm
[53:00] B here were asked to relax that and I'm giving you the power of 90% and saying
[53:03] giving you the power of 90% and saying calculate the sample size I've said here
[53:07] calculate the sample size I've said here that it's under a balanced design and
[53:09] that it's under a balanced design and there I mean to say that the number of
[53:12] there I mean to say that the number of observations in each group is the same
[53:14] observations in each group is the same so that'll simplify some of the
[53:16] so that'll simplify some of the calculations for us so what total sample
[53:19] calculations for us so what total sample size under a balanced design what we
[53:21] size under a balanced design what we need to provide a power of 90% okay
[53:27] need to provide a power of 90% okay so feel free to if you're really
[53:30] so feel free to if you're really thinking you've got a handle on all this
[53:32] thinking you've got a handle on all this stuff have a go at answering this but we
[53:35] stuff have a go at answering this but we haven't quite dealt with some of this
[53:36] haven't quite dealt with some of this formula yet so I I'm not too concerned
[53:40] formula yet so I I'm not too concerned if you want to just sit back and watch
[53:41] if you want to just sit back and watch me do this because yeah it is quite
[53:43] me do this because yeah it is quite difficult but having done this you'll
[53:45] difficult but having done this you'll really get a sense of how some of these
[53:46] really get a sense of how some of these calculations get done and just again
[53:50] calculations get done and just again another forewarning I tend not to just
[53:52] another forewarning I tend not to just throw formula at you and ask you to fill
[53:55] throw formula at you and ask you to fill and ask you to substitute in figures
[53:58] and ask you to substitute in figures into the formula I'm really coming at
[54:00] into the formula I'm really coming at this from first principles so your
[54:02] this from first principles so your textbook might provide a formula it's
[54:04] textbook might provide a formula it's like sample size calculation N equals
[54:07] like sample size calculation N equals blah and you're subbing everything I am
[54:09] blah and you're subbing everything I am not really approaching it like that I'm
[54:11] not really approaching it like that I'm really going to try to take this take
[54:13] really going to try to take this take the first principles approach to this
[54:15] the first principles approach to this which hopefully the fruits of which will
[54:17] which hopefully the fruits of which will be you having a really solid
[54:19] be you having a really solid understanding of how everything comes
[54:21] understanding of how everything comes together
[54:24] all right so the first thing is to assess what the null hypothesis is going
[54:28] assess what the null hypothesis is going to be and that's that theta is equal to
[54:31] to be and that's that theta is equal to 0 our alternate hypothesis will be that
[54:34] 0 our alternate hypothesis will be that theta is greater than 0 because it's a
[54:37] theta is greater than 0 because it's a one tailed test now what I've done here
[54:42] one tailed test now what I've done here is I've put these two curves
[54:43] is I've put these two curves side-by-side again to really give us an
[54:45] side-by-side again to really give us an impression of what's going on the curve
[54:49] impression of what's going on the curve in black here is the distribution of our
[54:51] in black here is the distribution of our test statistic we'd get if the null
[54:54] test statistic we'd get if the null hypothesis is true
[54:56] hypothesis is true so there's theta being 0 that's the
[54:58] so there's theta being 0 that's the difference between the two cohorts our
[55:01] difference between the two cohorts our sample statistic will have a mean of 0
[55:03] sample statistic will have a mean of 0 and some kind of variance about it
[55:06] and some kind of variance about it now if we're trying to say that in
[55:10] now if we're trying to say that in reality the true difference will be 10%
[55:13] reality the true difference will be 10% well this red curve will result and the
[55:17] well this red curve will result and the question is going to be how much of this
[55:19] question is going to be how much of this red curve is going to be to the right of
[55:22] red curve is going to be to the right of this yellow line and as we said before
[55:26] this yellow line and as we said before this shaded region here is going to be
[55:28] this shaded region here is going to be 5% because this null hypothesis well the
[55:32] 5% because this null hypothesis well the hypothesis test we're going to use
[55:33] hypothesis test we're going to use assumes that the null hypothesis is true
[55:36] assumes that the null hypothesis is true and we will reject that null hypothesis
[55:39] and we will reject that null hypothesis if we're in this upper 5% so if this red
[55:45] if we're in this upper 5% so if this red distribution is in reality what results
[55:48] distribution is in reality what results the proportion of that red distribution
[55:50] the proportion of that red distribution to the right of this yellow line will be
[55:52] to the right of this yellow line will be the ability for our test to pick up this
[55:55] the ability for our test to pick up this difference it's the ability of our test
[55:58] difference it's the ability of our test to reject the null hypothesis given that
[56:01] to reject the null hypothesis given that this really is that true difference so
[56:03] this really is that true difference so hopefully that's really ramming at home
[56:05] hopefully that's really ramming at home so basically that's what we're about to
[56:08] so basically that's what we're about to do we're about to try to find the
[56:09] do we're about to try to find the proportion of this curve the proportion
[56:13] proportion of this curve the proportion under the red curve that lies to the
[56:15] under the red curve that lies to the right of that yellow line so the first
[56:18] right of that yellow line so the first question might be well we need to find
[56:20] question might be well we need to find the variance of both of these two curves
[56:23] the variance of both of these two curves because don't forget this yellow line
[56:25] because don't forget this yellow line depends on the variance of the black
[56:28] depends on the variance of the black curve and then of course the area of the
[56:31] curve and then of course the area of the red curve to the right of that line
[56:33] red curve to the right of that line depends on the variance of the red curve
[56:36] depends on the variance of the red curve so we're going to need to know both so
[56:38] so we're going to need to know both so the variance of the black one this
[56:39] the variance of the black one this assumes the null hypothesis is true such
[56:42] assumes the null hypothesis is true such that both peas both proportions are the
[56:46] that both peas both proportions are the same in each cohort so that's why we
[56:48] same in each cohort so that's why we have P times 1 minus P here on n 1 plus
[56:52] have P times 1 minus P here on n 1 plus P times 1 minus P on n naught we saw
[56:54] P times 1 minus P on n naught we saw that in a previous section the variance
[56:58] that in a previous section the variance of H 1 so that is this red curve here is
[57:00] of H 1 so that is this red curve here is going to be this one here P 1 times 1
[57:04] going to be this one here P 1 times 1 minus P 1 plus P naught times 1 minus P
[57:06] minus P 1 plus P naught times 1 minus P naught so we allow them to be different
[57:07] naught so we allow them to be different in each case now because we've actually
[57:10] in each case now because we've actually specified and this is going to help us
[57:12] specified and this is going to help us with calculations obviously we've
[57:14] with calculations obviously we've specified what the proportions of good
[57:17] specified what the proportions of good outcomes are for the non-operative group
[57:21] outcomes are for the non-operative group we've said that it starts at 50% that's
[57:23] we've said that it starts at 50% that's what we expect the physio only group to
[57:25] what we expect the physio only group to be and we're going to test to see
[57:27] be and we're going to test to see whether we can detect a difference where
[57:31] whether we can detect a difference where our operative cohort goes up to 60% so
[57:34] our operative cohort goes up to 60% so this value of P I'm going to put in here
[57:36] this value of P I'm going to put in here is 50% and it's slightly different to
[57:39] is 50% and it's slightly different to what we used in a previous slide where
[57:41] what we used in a previous slide where we kind of averaged the two but don't
[57:43] we kind of averaged the two but don't forget the null hypothesis here isn't
[57:45] forget the null hypothesis here isn't simply that the two are equal we're kind
[57:49] simply that the two are equal we're kind of saying that the two are equal but
[57:50] of saying that the two are equal but they're equal at 50% we've kind of
[57:54] they're equal at 50% we've kind of specified that so 0.5 times 0.5 divided
[57:58] specified that so 0.5 times 0.5 divided by 400 plus 0.5 times 0.5 divided by 400
[58:01] by 400 plus 0.5 times 0.5 divided by 400 400 being the number of observations in
[58:04] 400 being the number of observations in each of the respective groups so we can
[58:07] each of the respective groups so we can actually find the answer to that and
[58:08] actually find the answer to that and that's 0.001 to 5 so that would be the
[58:11] that's 0.001 to 5 so that would be the variation also a the variance of the
[58:15] variation also a the variance of the black curve there and for H 1 we do the
[58:22] black curve there and for H 1 we do the same thing except it's going to be 0.6
[58:23] same thing except it's going to be 0.6 times 0.4 on the other one so the
[58:25] times 0.4 on the other one so the variance of the red curve is going to be
[58:27] variance of the red curve is going to be just slightly less feel free to check my
[58:31] just slightly less feel free to check my calculations if you want I'm pretty
[58:33] calculations if you want I'm pretty satisfied with them so now what we're
[58:36] satisfied with them so now what we're going to do is we're gonna let T 1 which
[58:38] going to do is we're gonna let T 1 which is our test statistic be the calculated
[58:41] is our test statistic be the calculated difference between the two groups which
[58:43] difference between the two groups which will be theta hat divided by the square
[58:46] will be theta hat divided by the square root of V H naught why is that the case
[58:50] root of V H naught why is that the case well don't
[58:51] well don't forget for a test statistic we we take
[58:53] forget for a test statistic we we take the difference and divide by the
[58:55] the difference and divide by the standard error right in this case it's
[58:57] standard error right in this case it's the square root of the variance so that
[59:01] the square root of the variance so that will allow us to put this black curve on
[59:04] will allow us to put this black curve on a scale of just a standardized normal
[59:08] a scale of just a standardized normal distribution so remember our last slide
[59:10] distribution so remember our last slide this this means that T 1 will be
[59:12] this this means that T 1 will be distributed with a mean of well theta
[59:15] distributed with a mean of well theta hat and a variance of 1 and a variance
[59:18] hat and a variance of 1 and a variance of 1 ok so what we're going to do now is
[59:21] of 1 ok so what we're going to do now is try to find the expected value of T 1
[59:24] try to find the expected value of T 1 and also the variance of T 1 bear with
[59:28] and also the variance of T 1 bear with me
[59:28] me we'll see where this goes but but
[59:30] we'll see where this goes but but essentially what's happening here is
[59:31] essentially what's happening here is that we're going to need to put both of
[59:33] that we're going to need to put both of these two curves on the same scale
[59:37] these two curves on the same scale it's no good comparing apples with
[59:39] it's no good comparing apples with oranges we want them on exactly the same
[59:41] oranges we want them on exactly the same scale and that scale is going to be our
[59:43] scale and that scale is going to be our test statistics scale t1 with a mean of
[59:46] test statistics scale t1 with a mean of 0 here the black curve and it'll have a
[59:49] 0 here the black curve and it'll have a variance of 1 so we've got to put this
[59:51] variance of 1 so we've got to put this red curve on that same scale so the
[59:56] red curve on that same scale so the expected value of t1 is the expected
[59:57] expected value of t1 is the expected value of theta hat on the square root of
[60:00] value of theta hat on the square root of the variance of H naught and in this
[60:03] the variance of H naught and in this case it's going to be 0.1 divided by
[60:06] case it's going to be 0.1 divided by well there's the square root of H naught
[60:08] well there's the square root of H naught or chuck it in there and you get 2 point
[60:11] or chuck it in there and you get 2 point 8 2 8 so this is the center of our red
[60:16] 8 2 8 so this is the center of our red curve on the new scale on the scale of
[60:20] curve on the new scale on the scale of our test statistic the red curve has an
[60:24] our test statistic the red curve has an expected value of two point eight two
[60:26] expected value of two point eight two eight and what's the variance of that
[60:28] eight and what's the variance of that red curve on our new scale well we're
[60:31] red curve on our new scale well we're gonna take the variance of t1 and we're
[60:34] gonna take the variance of t1 and we're going to just basically put the equation
[60:36] going to just basically put the equation for t1 in the brackets here and you'll
[60:38] for t1 in the brackets here and you'll note that it's the variance of theta hat
[60:40] note that it's the variance of theta hat divided by or the variance of this
[60:43] divided by or the variance of this character down here now that's a
[60:45] character down here now that's a constant term so we remember your little
[60:48] constant term so we remember your little rules about variance if you have a
[60:50] rules about variance if you have a variance of something which is a
[60:51] variance of something which is a constant term it comes out the front and
[60:54] constant term it comes out the front and gets squared so the variance of t1 which
[60:57] gets squared so the variance of t1 which is our red curve is going to be the
[61:00] is our red curve is going to be the variance of theta hat divided by V H
[61:04] variance of theta hat divided by V H naught
[61:06] naught so vh1 is the variance of our treatment
[61:09] so vh1 is the variance of our treatment difference but that's going to be that
[61:11] difference but that's going to be that variance assuming that difference of 0.1
[61:14] variance assuming that difference of 0.1 and V H naught assumes a difference of
[61:18] and V H naught assumes a difference of zero so we get V H one divided by V H
[61:22] zero so we get V H one divided by V H naught and because we have those
[61:24] naught and because we have those calculated up here on the top left we
[61:26] calculated up here on the top left we can just sub the sin and we get point
[61:28] can just sub the sin and we get point nine eight so what does that mean it
[61:30] nine eight so what does that mean it means that this red curve on the scale
[61:34] means that this red curve on the scale of this test statistic has an expected
[61:38] of this test statistic has an expected value of two point eight two eight and a
[61:42] value of two point eight two eight and a variance of 0.98 so this seems quite
[61:45] variance of 0.98 so this seems quite confusing but all we've really done is
[61:47] confusing but all we've really done is we noted that our hypothesis test will
[61:50] we noted that our hypothesis test will proceed with this black curve here and
[61:53] proceed with this black curve here and we know that we'll reject when we're up
[61:55] we know that we'll reject when we're up in this region but we want to know when
[61:59] in this region but we want to know when is this red curve lie on the same scale
[62:02] is this red curve lie on the same scale now we have it
[62:03] now we have it we know this red curve on the scale of
[62:06] we know this red curve on the scale of this hypothesis test here for the test
[62:09] this hypothesis test here for the test statistic on the scale of this test
[62:11] statistic on the scale of this test statistic has a mean of two point eight
[62:13] statistic has a mean of two point eight two eight and has a variance of 0.98 so
[62:17] two eight and has a variance of 0.98 so how handy is that now that we have all
[62:19] how handy is that now that we have all that information we know that this point
[62:21] that information we know that this point here is going to be one point six four
[62:23] here is going to be one point six four five because that is the that is the
[62:26] five because that is the that is the critical value that is provided when you
[62:28] critical value that is provided when you have a one tailed test to five percent
[62:31] have a one tailed test to five percent level of significance and we know that
[62:34] level of significance and we know that the expected value of this curve is two
[62:36] the expected value of this curve is two point eight to eight so all we're doing
[62:38] point eight to eight so all we're doing now is looking at a curve that has an
[62:40] now is looking at a curve that has an expected value of two point eight to
[62:42] expected value of two point eight to eight a variance of 0.98 and we want to
[62:45] eight a variance of 0.98 and we want to know what proportion of the curve is to
[62:46] know what proportion of the curve is to the right of one point six four five so
[62:53] the right of one point six four five so this is the easy bit now we just sub in
[62:55] this is the easy bit now we just sub in one minus this as a Phi which is the
[62:59] one minus this as a Phi which is the basically provides you the cumulative
[63:01] basically provides you the cumulative distribution function for a given Zed
[63:04] distribution function for a given Zed score which is a standardized normal
[63:06] score which is a standardized normal value so we're gonna go one point six
[63:09] value so we're gonna go one point six four five minus two point eight two
[63:11] four five minus two point eight two eight divided by the standard deviation
[63:13] eight divided by the standard deviation which is the square root of 0.98 so the
[63:17] which is the square root of 0.98 so the power is going to be one minus
[63:19] power is going to be one minus the CDF of negative 120 which happens to
[63:24] the CDF of negative 120 which happens to be 0.88 for one so the CDF essentially
[63:29] be 0.88 for one so the CDF essentially is just the amount of the distribution
[63:31] is just the amount of the distribution to the left of a given point on a normal
[63:34] to the left of a given point on a normal distribution so you can read that off
[63:36] distribution so you can read that off tables or you can use Excel your norm s
[63:39] tables or you can use Excel your norm s dist
[63:40] dist function on Excel our answer is 0.88 for
[63:45] function on Excel our answer is 0.88 for one okay so we're going to go back here
[63:47] one okay so we're going to go back here and we have eighty eight point four
[63:50] and we have eighty eight point four percent of this red distribution is lies
[63:53] percent of this red distribution is lies to the right of this yellow line and
[63:57] to the right of this yellow line and that indeed is the power of this test so
[64:02] that indeed is the power of this test so look you might find in textbooks you
[64:05] look you might find in textbooks you might get given formulas for this and
[64:07] might get given formulas for this and you can sub the stuff in you're
[64:08] you can sub the stuff in you're certainly welcome to use those but I
[64:11] certainly welcome to use those but I wanted to try my hand at really giving
[64:12] wanted to try my hand at really giving you a visualization of what's going on
[64:14] you a visualization of what's going on because I really don't like just saying
[64:16] because I really don't like just saying hey use a formula and then move on stats
[64:20] hey use a formula and then move on stats to be way more interesting than just
[64:21] to be way more interesting than just using the formula all the time so let's
[64:26] using the formula all the time so let's have a quick look at answer for Part B
[64:27] have a quick look at answer for Part B this one is now probably well depends
[64:30] this one is now probably well depends algebra heavy but it might be a little
[64:33] algebra heavy but it might be a little bit simpler conceptually all we do here
[64:36] bit simpler conceptually all we do here is we reset our values of the expected
[64:39] is we reset our values of the expected value of t1 and the variance of t1 we've
[64:43] value of t1 and the variance of t1 we've got those formulas there what we're
[64:46] got those formulas there what we're gonna do is redo what we just did but
[64:49] gonna do is redo what we just did but set the power to be 0.9 instead of well
[64:54] set the power to be 0.9 instead of well in our case we got zero point eight
[64:55] in our case we got zero point eight eight four so here we're gonna say zero
[64:58] eight four so here we're gonna say zero point nine is equal to one minus the CDF
[65:01] point nine is equal to one minus the CDF of this stuff here we're just subbing in
[65:04] of this stuff here we're just subbing in all the values for the expected value of
[65:06] all the values for the expected value of t1 and the variance of T 1 respectively
[65:09] t1 and the variance of T 1 respectively so you can see here the expected value
[65:11] so you can see here the expected value of t1 is this thing and the variance of
[65:13] of t1 is this thing and the variance of t1 is that with a big square root on it
[65:16] t1 is that with a big square root on it so I'm doing a few steps at once here
[65:18] so I'm doing a few steps at once here but we're just multiplying top and
[65:20] but we're just multiplying top and bottom by the square root of V H naught
[65:25] bottom by the square root of V H naught so I'll go through this pretty quickly
[65:29] to get rid of this CDF function we're
[65:32] to get rid of this CDF function we're essentially taking the inverse function
[65:35] essentially taking the inverse function of 0.1 the cumulative distribution
[65:37] of 0.1 the cumulative distribution inverse of 0.1 and you get minus one
[65:40] inverse of 0.1 and you get minus one point two eight one six so all the stuff
[65:45] point two eight one six so all the stuff in the brackets here will equal that now
[65:48] in the brackets here will equal that now it's about time we have to revisit V H
[65:50] it's about time we have to revisit V H naught and V H 1 so on the right here
[65:52] naught and V H 1 so on the right here we'll have a quick look at what those
[65:54] we'll have a quick look at what those were V H naught was this character here
[65:57] were V H naught was this character here or the square root of V H naught happens
[65:59] or the square root of V H naught happens to be this but notice how we have N 1
[66:02] to be this but notice how we have N 1 and n 2 I mentioned in the question here
[66:06] and n 2 I mentioned in the question here that we're looking for a balanced design
[66:07] that we're looking for a balanced design so this is where it's going to simplify
[66:09] so this is where it's going to simplify a little bit n 1 it can be written as
[66:12] a little bit n 1 it can be written as just n on 2 so the total number of
[66:16] just n on 2 so the total number of observations divided by 2 and so 2 can
[66:19] observations divided by 2 and so 2 can end - I've just realized I've used n 0
[66:23] end - I've just realized I've used n 0 in the previous slide but that's ok same
[66:25] in the previous slide but that's ok same thing so each of these will be the total
[66:29] thing so each of these will be the total number of observations divided by 2
[66:30] number of observations divided by 2 because we have a balanced design and if
[66:33] because we have a balanced design and if you meter all that out you get 1 on the
[66:36] you meter all that out you get 1 on the square root of n similarly for vh1
[66:39] square root of n similarly for vh1 you'll get in this case the square root
[66:42] you'll get in this case the square root of 0.98 over the square root of n so
[66:46] of 0.98 over the square root of n so I'll put that in a little in a little
[66:47] I'll put that in a little in a little box and we're just about to substitute
[66:49] box and we're just about to substitute in the square root of V H naught and the
[66:51] in the square root of V H naught and the square root of V H 1 into our equation
[66:53] square root of V H 1 into our equation here on the left and rearrange do a
[66:57] here on the left and rearrange do a little bit of algebra and we're going to
[66:58] little bit of algebra and we're going to find that n is equal to 84 point 8.9 so
[67:05] find that n is equal to 84 point 8.9 so the number of observations that allows
[67:07] the number of observations that allows us to have a power of 0.9 is going to be
[67:11] us to have a power of 0.9 is going to be 8 48.9 now I've actually rounded this up
[67:16] 8 48.9 now I've actually rounded this up to 850 because you're gonna have a
[67:19] to 850 because you're gonna have a you're gonna have to have a whole number
[67:20] you're gonna have to have a whole number of people in each group so it has to be
[67:23] of people in each group so it has to be divisible by 2 and of course when we do
[67:26] divisible by 2 and of course when we do sample size calculations you always
[67:28] sample size calculations you always round upwards
[67:29] round upwards so 850 is going to be our man meaning
[67:32] so 850 is going to be our man meaning that we'll have 425 observations in each
[67:36] that we'll have 425 observations in each group so with the sample size that's
[67:38] group so with the sample size that's slightly larger than what we had in the
[67:41] slightly larger than what we had in the first question it'll allow us to get a
[67:43] first question it'll allow us to get a power
[67:43] power which is also slightly larger gives us
[67:46] which is also slightly larger gives us more power in our test all right
[67:51] more power in our test all right congratulations you made it my goodness
[67:54] congratulations you made it my goodness what a hopefully you've got through
[67:56] what a hopefully you've got through unscathed
[67:57] unscathed but if you've got any questions I feel
[67:59] but if you've got any questions I feel free to put them down in the comments of
[68:01] free to put them down in the comments of the video or you can type up on the
[68:04] the video or you can type up on the discussion board on the Uni discussion
[68:05] discussion board on the Uni discussion board and as I said at the beginning all
[68:07] board and as I said at the beginning all videos in the series and other
[68:09] videos in the series and other statistical videos can be found on Zed
[68:11] statistical videos can be found on Zed statistics com thanks for watching
