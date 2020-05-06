# Packit Service Web UI
Development moved to separated [Dashboard project](https://github.com/packit-service/dashboard)


## UI

### Utils

* SCSS is a superset of CSS with variable support and better query selection. It is compiled to _readable_ CSS.

### UI/UX

Patternfly has two official variants.

* Patternfly HTML: Its a CSS Framework. Zero inbuilt support for JavaScript. User has to take care of interactive components + animations themselves.
* Patternfly React: Complete UI toolkit. Components are interactive by default. Inbuilt support for charts and datatables, which follow a similar design pattern.

Note: They also have a slack for community support.

## Routing and Templating

We have multiple options availible for routing (url handling, changing pages) and templating. 

Patternfly has official React bindings so I'm just skipping discussion about React alternatives.


### 1) Only React: 
Since the dashboard will fetch all data from the API, we can make it entirely client side. Using Fetch/Axios, the browser will fetch the json directly from the API, no middleman involved. Controlling the routes in the URL is possible beacuse react-router uses the HTML5 History API. After compiling the JSX to JS, we will have static HTML/CSS/JS which can be served from apache, nginx etc or even GitHub pages.

#### Pros
* Serving static files is faster than wsgi + python. 
* One language for everything.
* Single page web app.
* Using React + Patternfly's extra React only features like charts and datatables is leaner than importing Patternfly HTML + jQuery + some charts library + datatables library + other plugins.


#### Cons
* Might not be extensible. There will be a lot of extra work if we ever need to add a backend feature that can't be done via the **public** API
* Using a JavaScript framework is bad for SEO. 
* Specifying the packit-service deployment link via environment variable is simply not possible without using a backend like Flask. We will have to hardcode the API URL.
* A large json file from the API will cause slower loading because the clients's browser will have to fetch it entirely before parsing it. (Not a major issue since our API supports pagination and we can modify the API)
* We will have to remake the deployment playbooks beacuse we eliminated the python part.



### 2) Flask + React:
Unlike Angular or Vue frameworks, React is a library. We can call it when needed, for selective pages or even parts of a page. We will fetch items from the API, directly to the browser but when needed we have the ability to do API -> Flask Server -> Browser (like we do currently, as of May 2020).

Routes can be rendered by both Flask and React.

#### Pros
* This is extensible and we can add backend features whenever we need.
* Deployment process does not change.
* Single page web app.
* Using React + Patternfly's extra React only features like charts and datatables is leaner than importing Patternfly HTML + jQuery + some charts library + datatables library + other plugins.

#### Cons
* Codebase (and tests) will be split across multiple languages.


### 3) Flask
This is what we are doing currently (May 2020). All the templating + routing logic will be handled server side. JavaScript will still be used but not for routing or rendering the contents. If we go with this, I suggest using Bootstrap + Themes over Patternfly HTML because Patternfly HTML does not have any default behaviour for UI components unlike Bootstrap which provides basic inbuilt javascript for interactivity.

#### Pros
* It will somewhat work even with JavaScript disabled.
* Reliable, just works, less setup for development.

#### Cons
* We will have to use more third party libs for charts, datatables which might not provide a consistent look. (Or we can import the charts component of patternfly-react, making this a subset of option 2)
* The entire page will load when going to another page instead of loading just a part of the page.


