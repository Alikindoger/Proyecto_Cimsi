# GUIA REPOSITORIO GIT

## Filosofía organizativa
    Usaremos una estrucutra monorepo.(Figura 1) Esto facilita ver el progreso de los demás y
    combinar los diferentes subproyectos.

```text
proyecto_cimsi/
├── .git/                   
├── .gitignore              #.gitignore global
├── docs/                   #Documentación compartida        
├── README.md               #Readme global
├── subproyecto-1/        
│   ├── .gitignore          #.gitignore para subproyecto-1/
│   ├── README.md           #Readme para subproyecto-1/
│   ├── docs/               #Documentación para subproyecto-1/
│   └── src/                #Archivos de desarrollo del subproyecto 1
├── subproyecto-2/       
│   ├── .gitignore         
│   ├── README.md
│   ├── docs/            
│   └── src/
└── shared/                # Recursos compartidos
```


## ¿Qué nos motiva?
     Creemos que aportará de manera muy positiva tener un git
     de forma complementaria a la documentación vayamos generando.

## Guia developers
### 1.1 Empezando
- Clonar el repositorio
- Configurar tu readme
- Migrar el progreso actual (si procede) a la carpeta src
- Migrar documentación (si procede) a la carpeta docs 
### 1.2 Día a día
    Para actualizar el git y subir vuestro progreso podeís usar los siguientes comandos:
- git add  your_folder_name/
- git commit "Tu_subproyecto: nombre_commit"
