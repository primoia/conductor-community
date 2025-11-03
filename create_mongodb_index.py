#!/usr/bin/env python3
"""
Script to create MongoDB index for optimizing soft-delete queries on history collection
"""

from pymongo import MongoClient, ASCENDING
import os
import sys

# MongoDB connection settings
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGODB_DB", "conductor")

def create_history_indexes():
    """Create indexes on history collection for performance optimization"""

    try:
        # Connect to MongoDB
        print(f"Connecting to MongoDB at {MONGO_URI}...")
        client = MongoClient(MONGO_URI)
        db = client[MONGO_DB]

        # Get history collection
        history_collection = db["history"]

        print("\nCurrent indexes on 'history' collection:")
        existing_indexes = list(history_collection.list_indexes())
        for idx in existing_indexes:
            print(f"  - {idx['name']}: {idx['key']}")

        # Create compound index for instance_id + isDeleted
        print("\nCreating compound index: {instance_id: 1, isDeleted: 1}...")
        index_name = history_collection.create_index(
            [("instance_id", ASCENDING), ("isDeleted", ASCENDING)],
            name="instance_id_1_isDeleted_1"
        )
        print(f"✅ Index created: {index_name}")

        # Optional: Create index for deleted_at for cleanup queries
        print("\nCreating index: {deleted_at: 1}...")
        index_name2 = history_collection.create_index(
            [("deleted_at", ASCENDING)],
            name="deleted_at_1",
            sparse=True  # Only index documents that have deleted_at
        )
        print(f"✅ Index created: {index_name2}")

        print("\n" + "="*60)
        print("  INDEX CREATION COMPLETED")
        print("="*60)

        # Show all indexes after creation
        print("\nAll indexes on 'history' collection:")
        all_indexes = list(history_collection.list_indexes())
        for idx in all_indexes:
            print(f"  - {idx['name']}: {idx['key']}")
            if 'sparse' in idx:
                print(f"    sparse: {idx['sparse']}")

        # Show collection stats
        stats = db.command("collStats", "history")
        print(f"\nCollection stats:")
        print(f"  - Documents: {stats.get('count', 0):,}")
        print(f"  - Storage size: {stats.get('storageSize', 0) / 1024 / 1024:.2f} MB")
        print(f"  - Total indexes: {stats.get('nindexes', 0)}")
        print(f"  - Total index size: {stats.get('totalIndexSize', 0) / 1024 / 1024:.2f} MB")

        client.close()
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def explain_benefits():
    """Explain the benefits of the created indexes"""
    print("\n" + "="*60)
    print("  INDEX BENEFITS")
    print("="*60)
    print("""
1. Compound Index {instance_id: 1, isDeleted: 1}:
   - Optimizes soft-delete propagation queries
   - Speeds up filtering messages by instance and deletion status
   - Used by queries like: db.history.find({instance_id: "...", isDeleted: true})
   - Essential for performance when deleting instances with many messages

2. Index {deleted_at: 1} (sparse):
   - Optimizes cleanup/maintenance queries
   - Enables efficient queries to find old deleted messages
   - Sparse index saves space (only indexes docs with deleted_at field)
   - Useful for future cleanup jobs: "delete messages deleted > 90 days ago"

Performance Impact:
- Query time reduction: O(n) → O(log n)
- Memory usage: Minimal (sparse indexes)
- Write overhead: Negligible (only on updates with indexed fields)
    """)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  MONGODB INDEX CREATION SCRIPT")
    print("="*60)
    print("\nThis script creates optimized indexes for soft-delete")
    print("propagation on the 'history' collection")
    print("\nBased on: requisitos_propagacao_soft_delete.md")

    # Create indexes
    success = create_history_indexes()

    if success:
        explain_benefits()
        print("\n✅ Setup complete! Your soft-delete queries are now optimized.")
    else:
        print("\n⚠️  Index creation failed. Please check the error above.")
        sys.exit(1)
