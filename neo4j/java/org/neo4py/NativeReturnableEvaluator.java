package org.neo4py;

import org.neo4j.graphdb.TraversalPosition;
import org.neo4j.graphdb.ReturnableEvaluator;


public class NativeReturnableEvaluator implements ReturnableEvaluator {
	public NativeReturnableEvaluator() {
	}
	
	public native boolean isReturnableNode(TraversalPosition pos);
}