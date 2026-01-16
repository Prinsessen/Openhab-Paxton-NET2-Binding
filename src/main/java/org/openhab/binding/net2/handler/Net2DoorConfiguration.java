/*
 * Copyright (c) 2010-2026 Contributors to the openHAB project
 *
 * See the NOTICE file(s) distributed with this work for additional
 * information.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0
 *
 * SPDX-License-Identifier: EPL-2.0
 */
package org.openhab.binding.net2.handler;

import org.eclipse.jdt.annotation.NonNullByDefault;

/**
 * Configuration class for Net2 Door thing.
 *
 * @author OpenHAB Community - Initial contribution
 */
@NonNullByDefault
public class Net2DoorConfiguration {
    public Integer doorId = 0;
    public String name = "";
}
