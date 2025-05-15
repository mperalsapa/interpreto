// connect to admin db
db = db.getSiblingDB("admin");

// create backend user
db.createUser({
    user: "frontend-service",
    pwd: "frontend-service",
    roles: [
        {
            role: "readWrite",
            db: "media_service"
        }
    ]
});

// connect to media_service db
db = db.getSiblingDB("media_service");

// create collections
db.createCollection("file");

// unique index to avoid duplicates
db.file.createIndex({ hash: 1 }, { unique: true });
