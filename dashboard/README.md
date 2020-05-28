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


### 4) Grafana Research + Observations 

Quick setup for experimentation. Default username/password: admin

```
podman run -d -p 8300:3000 -u="root"  --name=grafana -v /home/icewreck/Development/Packit/grafana:/var/lib/grafana:z grafana/grafana
```

* Grafana was built for and is suited towards real time data monitoring, time series analytics or something that changes very frequently (network or sensor data, system load, etc), but can be for other purposes.
* It has the concept of single page dashboards i.e. you host multiple services and then use a single instance of grafana to monitor all of them. Each service is supposed to have a seperate page/dashboard. Dashbords for different services can be installed from their [dashboard store.](https://grafana.com/grafana/dashboards?orderBy=name&direction=asc)
* Its a visualization software with little support for other data and we will have to make lots of custom widgets/plugins 
* Looks cool!
* Grafana fetches data by directly plugging into a database (called a data-source), so we will have to provide credentials to packit-service's postgres. We will have to provide raw SQL commands for every graph and these will have to be changed every time we modify our models.py file.
* Even postgres feels like a second class citizen compared to [time series databases.](https://grafana.com/docs/grafana/latest/getting-started/timeseries/)
* Alternatively, grafana can use our JSON API as a data-source but thats only possible by using a third party plugin. (https://grafana.com/grafana/plugins/simpod-json-datasource)
* There is no way of adding buttons or formatting inside tables (It may be possible, but I cannot find it) unless we make our own plugins for a customizable table. 
* Grafana stores layout configuration and all fetched data in its own database (sqlite by default) which is redundant because we store all build data in the packit-service postgresql database as well.
* Backup and restore will be difficult. (unless we use sqlite as database and copy-paste that sqlite file) (Edit: Incorrect, layout can be exported to json which can be copy -pasted into the correct folder for recreation)
* Recreating the dashboard from CI will be difficult as layouts are stored in the above mentioned database. (Edit: Incorrect, look at https://github.com/acouvreur/ssh-log-to-influx A standalone grafana instance along with this dashboard can be created via scripts)
* It has a cli but it can only change settings or passwords and install plugins.
* We cannot remove the _upgrade to grafana enterprise banner_ in the settings panel.
* Replacing the grafana logo in the title bar with packit's own is not possible. (unless we edit the source, which is hacky and not ideal)
* Help menu, login button, settings icon, documentation buttons cannot be removed.
* Large, publically visible buttons point to grafana documentation, which will be misleading in packit-service's dashboard.
* We cannot control the URL scheme.
* I haven't found a way to do something like recursive json.  Eg: (GET and display all builds info and if a user a wants it, find build_id from the all builds json and then do a GET request to fetch another json file for detailed info regarding that build_id)
* Tests ?
* Adapting it for our use case will be a literal hackfest with tons of plugins thrown in to make it work.



## Dashboard - List of Features

### Home Page

* Number of successful and failed builds. (bar chart with dual bars for successful/failed) (toggle for weekly/monthly/yearly)
* Number of successful out of total builds of all time. (donut chart)
* Total number of projects (100% filled donut chart)
* Total number of installations (100% filled donut chart)
* Manually triggered vs automatic builds. (line chart) (toggle for weekly/monthly/yearly)
* Top 5 most active projects. (Data List) (toggle for weekly/monthly/all-time)
* Builds per chroot (donut chart)
* Testing farm usage chart

### Jobs Page
A searchable, sortable datatable listing all the [jobs](https://packit.dev/docs/configuration/#packit-service-jobs) executed by packit service. 
Fields:
* Job Type (tests or copr_build)
* Trigger (Link to PR or release which triggered this)
* Choots and their status
* Git Ref
* Pull Requests
* Web Logs URL
* Build ID
* Repo Name and Link 

### Build Info Page

* Package/Project Name
* SRPM Name
* Repository URL
* Link to trigger (pull request or release)
* Copr Build ID
* PR ID (where applicable)
* Project ID
* Build Submitted, Started, Finished Time
* List of chroots
* Status per chroot
* Instructions to quick enable and install that build
* List + download link of built RPMS, their size, etc
* Link to the testing farm results page.
* Link to the logs page.

#### Build Logs Page

* Once a build has finished, copr creates a web directory listing with downloadable build related files like some log files, the built rpms, etc. 
* The build logs are in text files like build.log.gz and builder-live.log.gz 
* These files will be rendered on the logs page inside some sort of monospace text widget.
* SRPM logs, build logs and the live builder log (tabs to switch between them).
* Dropdown to switch between the log pages of chroots/targets of the same build id.


### Projects Page

* Total number of projects (100% filled donut chart)
* Small gallery style cards for every project. (filters to sort by most builds, user namespace, recent activity)

#### Specific Project View

* Project ID
* Total Number of PRs that used packit-service
* Total number of builds
* List of all builds related to that projects, from newest to oldest. (data list)
* Each build will open the detailed build view

### Status

* Packit Service status and downtime reports.
* Total number of calls to the GitHub API per hour. (sparkline chart)
* Number of fedmsgs per hour. (sparkline chart)

### Installations
List of namespaces and then a collapsable sublist of repos which have packit-service enabled.

### Testing Farm
(To be added later)

### Caching
* Cache common API requests in the dashboard so as to not overload packit-service with repititive requests. 
* Sqlite [can run in-memory](https://sqlite.org/inmemorydb.html) for caching. 
* There is also [Flask-Caching](https://pythonhosted.org/Flask-Caching/) but it requires additional backends which might be overkill.
* (We might not need this at all) 

### FAQ

The FAQ page will either link to the FAQ page on packit.dev or just live-render the [FAQ markdown file](https://github.com/packit-service/packit.dev/blob/master/content/faq/_index.md) from the packit.dev repo on the dashbpoard. This way we can have a single content source while respecting the desogn scheme of both the website and the dashboard.

### About

## API 
* /pull-requests endpoint
* /projects endpoint (possibly merge with the installations endpoint)
* Fetch selective copr builds instead of all of them in the builds list (https://github.com/packit-service/packit-service/issues/633)
* Other API endpoints for charts, stats, etc. (Discuss later)


