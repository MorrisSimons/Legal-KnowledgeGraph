# Legal Knowledge Graph


![top language](https://img.shields.io/github/languages/top/gpt-null/template)
![code size](https://img.shields.io/github/languages/code-size/gpt-null/template)
![last commit](https://img.shields.io/github/last-commit/gpt-null/template)
![issues](https://img.shields.io/github/issues/gpt-null/template)
![contributors](https://img.shields.io/github/contributors/gpt-null/template)
![License](https://img.shields.io/github/license/gpt-null/template)


Hello, in an attempt to make my work more transparent im going to share my progress here. This is a project im currently working on.


so, in very simple Sudo law what im trying to do is like the follwoing images say.

![Screenshot](assets/screenshot.png)


The fist image is here to show that data of what is connected is stored in diffrent places, for example, the law and a high court ruling case that is connected to the law.



![Screenshot](assets/screenshot_2.png)



This image is more to demonstrate the idea of the graph. Where you can connect different laws to foreign laws, such as European Union law and other laws. So for example, you want to draft a legal document. It can find the corresponding laws and terms, for example, vacation rights in the other country. 


Also, connect different high court rulings to those laws to check for legal edge cases. The gigster examples are just to give an easy explanation of what im trying to do. An LLM (or agent or whatever) can then dig deeper, for example, a gigster in not classified as an employee in Sweden. Then connect the classifications of what an employee is in Sweden. etc.

We also have other laws that affect vacation rights, such as laws for radiological workers or military workers in Sweden.

We also have paragraphs on the law with its own connections to different contexts.



you also laws that are changes to the old laws. [like this law](https://www.lagboken.se/lagboken/start/arbetsratt-och-arbetsmiljoratt/semesterlag-1977480/d_1851956-sfs-2013_950-lag-om-andring-i-semesterlagen-1977_480/) on this law [here](https://www.lagboken.se/lagboken/lagar-och-forordningar/lagar-och-forordningar/rattsvasende/rattegang-och-annan-process/rattegangsregler/gallande/d_889-lag-1974_371-om-rattegangen-i-arbetstvister/)

### Important Note

- The reality is much more complex here. 


TODO:
- [ ] Right now im just scraping legal documents.
- [ ] Then, transform the data, play around with how we are going to model it.
  
