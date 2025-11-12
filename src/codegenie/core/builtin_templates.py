"""
Built-in templates for common project types.

This module provides pre-configured templates for:
- Python projects (FastAPI, Django, Flask)
- JavaScript projects (React, Next.js, Express)
- Go projects
- Rust projects
"""

from .template_manager import (
    Template,
    TemplateMetadata,
    TemplateFile,
    TemplateType,
)


def get_fastapi_template() -> Template:
    """Get FastAPI project template."""
    return Template(
        metadata=TemplateMetadata(
            name="python-fastapi",
            version="1.0.0",
            description="FastAPI REST API project with async support",
            author="CodeGenie",
            tags=["python", "fastapi", "api", "async"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "app",
            "app/api",
            "app/models",
            "app/services",
            "tests",
        ],
        files=[
            TemplateFile(
                path="app/__init__.py",
                content="",
            ),
            TemplateFile(
                path="app/main.py",
                content='''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="${project_name}", version="${version}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to ${project_name}"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
            ),
            TemplateFile(
                path="app/api/__init__.py",
                content="",
            ),
            TemplateFile(
                path="requirements.txt",
                content='''fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.4.0
python-dotenv>=1.0.0
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
uvicorn app.main:app --reload
```

## API Documentation

Visit http://localhost:8000/docs for interactive API documentation.

## License

${license}
''',
            ),
            TemplateFile(
                path=".env.example",
                content='''DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./app.db
''',
            ),
        ],
        variables={
            "project_name": "My FastAPI Project",
            "description": "A FastAPI REST API project",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=["fastapi", "uvicorn[standard]", "pydantic", "python-dotenv"],
        dev_dependencies=["pytest", "pytest-asyncio", "httpx", "black", "flake8"],
    )


def get_django_template() -> Template:
    """Get Django project template."""
    return Template(
        metadata=TemplateMetadata(
            name="python-django",
            version="1.0.0",
            description="Django web application with REST framework",
            author="CodeGenie",
            tags=["python", "django", "web", "orm"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "config",
            "apps",
            "static",
            "media",
            "templates",
        ],
        files=[
            TemplateFile(
                path="manage.py",
                content='''#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
''',
            ),
            TemplateFile(
                path="requirements.txt",
                content='''Django>=4.2.0
djangorestframework>=3.14.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.0
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
pip install -r requirements.txt
python manage.py migrate
```

## Usage

```bash
python manage.py runserver
```

## License

${license}
''',
            ),
        ],
        variables={
            "project_name": "My Django Project",
            "description": "A Django web application",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=["django", "djangorestframework", "python-dotenv", "psycopg2-binary"],
        dev_dependencies=["pytest", "pytest-django", "black", "flake8"],
    )


def get_flask_template() -> Template:
    """Get Flask project template."""
    return Template(
        metadata=TemplateMetadata(
            name="python-flask",
            version="1.0.0",
            description="Flask web application",
            author="CodeGenie",
            tags=["python", "flask", "web"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "app",
            "app/routes",
            "app/models",
            "app/templates",
            "tests",
        ],
        files=[
            TemplateFile(
                path="app/__init__.py",
                content='''from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    @app.route('/')
    def index():
        return {'message': 'Welcome to ${project_name}'}
    
    @app.route('/health')
    def health():
        return {'status': 'healthy'}
    
    return app
''',
            ),
            TemplateFile(
                path="run.py",
                content='''from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
''',
            ),
            TemplateFile(
                path="requirements.txt",
                content='''Flask>=3.0.0
flask-sqlalchemy>=3.1.0
python-dotenv>=1.0.0
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python run.py
```

## License

${license}
''',
            ),
        ],
        variables={
            "project_name": "My Flask Project",
            "description": "A Flask web application",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=["flask", "flask-sqlalchemy", "python-dotenv"],
        dev_dependencies=["pytest", "pytest-flask", "black", "flake8"],
    )


def get_react_template() -> Template:
    """Get React project template."""
    return Template(
        metadata=TemplateMetadata(
            name="javascript-react",
            version="1.0.0",
            description="React application with Vite",
            author="CodeGenie",
            tags=["javascript", "react", "vite", "frontend"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "src",
            "src/components",
            "src/hooks",
            "src/utils",
            "public",
        ],
        files=[
            TemplateFile(
                path="index.html",
                content='''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>${project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
''',
            ),
            TemplateFile(
                path="src/main.jsx",
                content='''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''',
            ),
            TemplateFile(
                path="src/App.jsx",
                content='''import React from 'react'

function App() {
  return (
    <div>
      <h1>Welcome to ${project_name}</h1>
      <p>${description}</p>
    </div>
  )
}

export default App
''',
            ),
            TemplateFile(
                path="vite.config.js",
                content='''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
''',
            ),
            TemplateFile(
                path="package.json",
                content='''{
  "name": "${project_name}",
  "version": "${version}",
  "description": "${description}",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0"
  }
}
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
npm install
```

## Usage

```bash
npm run dev
```

## Build

```bash
npm run build
```

## License

${license}
''',
            ),
        ],
        variables={
            "project_name": "my-react-app",
            "description": "A React application",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=["react", "react-dom"],
        dev_dependencies=["vite", "@vitejs/plugin-react", "eslint", "prettier"],
    )


def get_nextjs_template() -> Template:
    """Get Next.js project template."""
    return Template(
        metadata=TemplateMetadata(
            name="javascript-nextjs",
            version="1.0.0",
            description="Next.js application with App Router",
            author="CodeGenie",
            tags=["javascript", "nextjs", "react", "ssr"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "app",
            "components",
            "lib",
            "public",
        ],
        files=[
            TemplateFile(
                path="app/page.js",
                content='''export default function Home() {
  return (
    <main>
      <h1>Welcome to ${project_name}</h1>
      <p>${description}</p>
    </main>
  )
}
''',
            ),
            TemplateFile(
                path="app/layout.js",
                content='''export const metadata = {
  title: '${project_name}',
  description: '${description}',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
''',
            ),
            TemplateFile(
                path="package.json",
                content='''{
  "name": "${project_name}",
  "version": "${version}",
  "description": "${description}",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "eslint": "^8.55.0",
    "eslint-config-next": "^14.0.0",
    "prettier": "^3.1.0"
  }
}
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
npm install
```

## Usage

```bash
npm run dev
```

## Build

```bash
npm run build
npm start
```

## License

${license}
''',
            ),
        ],
        variables={
            "project_name": "my-nextjs-app",
            "description": "A Next.js application",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=["next", "react", "react-dom"],
        dev_dependencies=["eslint", "eslint-config-next", "prettier"],
    )


def get_express_template() -> Template:
    """Get Express project template."""
    return Template(
        metadata=TemplateMetadata(
            name="javascript-express",
            version="1.0.0",
            description="Express REST API server",
            author="CodeGenie",
            tags=["javascript", "express", "api", "backend"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "src",
            "src/routes",
            "src/controllers",
            "src/models",
            "tests",
        ],
        files=[
            TemplateFile(
                path="src/index.js",
                content='''const express = require('express')
const cors = require('cors')
require('dotenv').config()

const app = express()
const port = process.env.PORT || 3000

app.use(cors())
app.use(express.json())

app.get('/', (req, res) => {
  res.json({ message: 'Welcome to ${project_name}' })
})

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' })
})

app.listen(port, () => {
  console.log(`Server running on port ${port}`)
})
''',
            ),
            TemplateFile(
                path="package.json",
                content='''{
  "name": "${project_name}",
  "version": "${version}",
  "description": "${description}",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0",
    "dotenv": "^16.3.0",
    "cors": "^2.8.5"
  },
  "devDependencies": {
    "nodemon": "^3.0.0",
    "jest": "^29.7.0",
    "supertest": "^6.3.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0"
  }
}
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
npm install
```

## Usage

```bash
npm run dev
```

## License

${license}
''',
            ),
        ],
        variables={
            "project_name": "my-express-api",
            "description": "An Express REST API",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=["express", "dotenv", "cors"],
        dev_dependencies=["nodemon", "jest", "supertest", "eslint", "prettier"],
    )


def get_go_cli_template() -> Template:
    """Get Go CLI project template."""
    return Template(
        metadata=TemplateMetadata(
            name="go-cli",
            version="1.0.0",
            description="Go command-line application",
            author="CodeGenie",
            tags=["go", "cli", "tool"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "cmd/${project_name}",
            "internal",
            "pkg",
        ],
        files=[
            TemplateFile(
                path="cmd/${project_name}/main.go",
                content='''package main

import "fmt"

func main() {
    fmt.Println("Welcome to ${project_name}")
}
''',
            ),
            TemplateFile(
                path="go.mod",
                content='''module ${project_name}

go 1.21

require (
)
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
go build -o ${project_name} ./cmd/${project_name}
```

## Usage

```bash
./${project_name}
```

## License

${license}
''',
            ),
        ],
        variables={
            "project_name": "my-go-cli",
            "description": "A Go CLI application",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=[],
        dev_dependencies=[],
    )


def get_go_web_template() -> Template:
    """Get Go web server template."""
    return Template(
        metadata=TemplateMetadata(
            name="go-web",
            version="1.0.0",
            description="Go web server application",
            author="CodeGenie",
            tags=["go", "web", "api"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "cmd/${project_name}",
            "internal",
            "pkg",
            "api",
        ],
        files=[
            TemplateFile(
                path="cmd/${project_name}/main.go",
                content='''package main

import (
    "fmt"
    "log"
    "net/http"
)

func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Welcome to ${project_name}")
    })
    
    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, `{"status": "healthy"}`)
    })
    
    log.Println("Server starting on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
''',
            ),
            TemplateFile(
                path="go.mod",
                content='''module ${project_name}

go 1.21

require (
)
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
go build -o ${project_name} ./cmd/${project_name}
```

## Usage

```bash
./${project_name}
```

## License

${license}
''',
            ),
        ],
        variables={
            "project_name": "my-go-web",
            "description": "A Go web server",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=[],
        dev_dependencies=[],
    )


def get_rust_cli_template() -> Template:
    """Get Rust CLI project template."""
    return Template(
        metadata=TemplateMetadata(
            name="rust-cli",
            version="1.0.0",
            description="Rust command-line application",
            author="CodeGenie",
            tags=["rust", "cli", "tool"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "src",
        ],
        files=[
            TemplateFile(
                path="src/main.rs",
                content='''fn main() {
    println!("Welcome to ${project_name}");
}
''',
            ),
            TemplateFile(
                path="Cargo.toml",
                content='''[package]
name = "${project_name}"
version = "${version}"
edition = "2021"

[dependencies]
clap = { version = "4.4", features = ["derive"] }
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
cargo build --release
```

## Usage

```bash
cargo run
```

## License

${license}
''',
            ),
        ],
        variables={
            "project_name": "my-rust-cli",
            "description": "A Rust CLI application",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=["clap"],
        dev_dependencies=[],
    )


def get_rust_web_template() -> Template:
    """Get Rust web server template."""
    return Template(
        metadata=TemplateMetadata(
            name="rust-web",
            version="1.0.0",
            description="Rust web server with Actix",
            author="CodeGenie",
            tags=["rust", "web", "actix", "api"],
            template_type=TemplateType.BUILTIN,
        ),
        directories=[
            "src",
            "src/handlers",
            "src/models",
        ],
        files=[
            TemplateFile(
                path="src/main.rs",
                content='''use actix_web::{get, App, HttpResponse, HttpServer, Responder};

#[get("/")]
async fn index() -> impl Responder {
    HttpResponse::Ok().body("Welcome to ${project_name}")
}

#[get("/health")]
async fn health() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({"status": "healthy"}))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("Server starting on http://127.0.0.1:8080");
    
    HttpServer::new(|| {
        App::new()
            .service(index)
            .service(health)
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
''',
            ),
            TemplateFile(
                path="Cargo.toml",
                content='''[package]
name = "${project_name}"
version = "${version}"
edition = "2021"

[dependencies]
actix-web = "4.4"
tokio = { version = "1.35", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
''',
            ),
            TemplateFile(
                path="README.md",
                content='''# ${project_name}

${description}

## Installation

```bash
cargo build --release
```

## Usage

```bash
cargo run
```

## License

${license}
''',
            ),
        ],
        variables={
            "project_name": "my-rust-web",
            "description": "A Rust web server",
            "version": "0.1.0",
            "license": "MIT",
        },
        dependencies=["actix-web", "tokio", "serde"],
        dev_dependencies=[],
    )


# Registry of all built-in templates
BUILTIN_TEMPLATES = {
    "python-fastapi": get_fastapi_template,
    "python-django": get_django_template,
    "python-flask": get_flask_template,
    "javascript-react": get_react_template,
    "javascript-nextjs": get_nextjs_template,
    "javascript-express": get_express_template,
    "go-cli": get_go_cli_template,
    "go-web": get_go_web_template,
    "rust-cli": get_rust_cli_template,
    "rust-web": get_rust_web_template,
}


def initialize_builtin_templates(template_manager) -> int:
    """
    Initialize all built-in templates in the template manager.
    
    Args:
        template_manager: TemplateManager instance
        
    Returns:
        Number of templates initialized
    """
    count = 0
    for name, template_func in BUILTIN_TEMPLATES.items():
        try:
            template = template_func()
            if template_manager.save_template(template, TemplateType.BUILTIN):
                count += 1
        except Exception as e:
            print(f"Error initializing template {name}: {e}")
    
    return count
