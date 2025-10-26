#!/usr/bin/env python3
"""
Script to cleanup obsolete MongoDB collections

Removes:
- apscheduler_jobs (not used - scheduler uses in-memory jobstore)
- councilor_executions (migrated to tasks collection with is_councilor_execution=True)
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import OperationFailure

# MongoDB connection settings
MONGODB_URL = os.environ.get('MONGODB_URL', 'mongodb://localhost:27017')
MONGODB_DB = os.environ.get('MONGODB_DB', 'conductor_state')

# Collections to remove
OBSOLETE_COLLECTIONS = [
    'apscheduler_jobs',
    'councilor_executions'
]


def main():
    print("=" * 80)
    print("🧹 Cleanup Obsolete MongoDB Collections")
    print("=" * 80)
    print()

    try:
        # Connect to MongoDB
        print(f"📡 Connecting to MongoDB: {MONGODB_URL}")
        client = MongoClient(MONGODB_URL)
        db = client[MONGODB_DB]

        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to database: {MONGODB_DB}")
        print()

        # Get all collections
        all_collections = db.list_collection_names()
        print(f"📋 Total collections in database: {len(all_collections)}")
        print()

        # Process each obsolete collection
        for collection_name in OBSOLETE_COLLECTIONS:
            print(f"🔍 Checking: {collection_name}")

            if collection_name not in all_collections:
                print(f"   ⚠️  Collection does not exist - skipping")
                print()
                continue

            collection = db[collection_name]
            count = collection.count_documents({})

            print(f"   📊 Documents: {count}")

            if count > 0:
                # Show sample document
                sample = collection.find_one()
                print(f"   📄 Sample document:")
                print(f"      {sample}")

            # Ask for confirmation
            response = input(f"   ❓ Remove collection '{collection_name}'? (yes/no): ").strip().lower()

            if response == 'yes':
                # Drop collection
                collection.drop()
                print(f"   ✅ Collection '{collection_name}' removed")
            else:
                print(f"   ⏭️  Skipped '{collection_name}'")

            print()

        # Show final state
        remaining_collections = db.list_collection_names()
        print("=" * 80)
        print(f"✅ Cleanup complete!")
        print(f"📋 Remaining collections ({len(remaining_collections)}):")
        for col in sorted(remaining_collections):
            count = db[col].count_documents({})
            print(f"   - {col} ({count} docs)")
        print("=" * 80)

    except OperationFailure as e:
        print(f"❌ MongoDB operation failed: {e}")
        print("   💡 Tip: Check if MongoDB requires authentication")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        if 'client' in locals():
            client.close()
            print("🔌 Disconnected from MongoDB")


if __name__ == '__main__':
    main()
