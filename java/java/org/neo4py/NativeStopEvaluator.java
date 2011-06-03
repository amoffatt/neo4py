package org.neo4py;

import org.neo4j.graphdb.TraversalPosition;
import org.neo4j.graphdb.StopEvaluator;


public class NativeStopEvaluator implements StopEvaluator {
	public NativeStopEvaluator() {
	}
	
	public native boolean isStopNode(TraversalPosition pos);
}